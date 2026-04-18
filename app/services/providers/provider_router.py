"""Smart provider router — city-aware, tier-aware, with two-level rerouting.

Routing rules:
    US (any tier)                   -> TextVerified (city via area code map)
    International + city + Pro/Custom -> Telnyx (filter[locality])
    International + city + PAYG     -> 5sim (city dropped, city_honoured=False)
    International + city + Freemium -> 402 before this is called
    International + no city         -> 5sim (cheapest)
    Failover on infrastructure errors only, not business errors.

Provider names never appear in user-facing errors.
"""

from typing import Optional, Tuple

from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.logging import get_logger
from app.services.providers.base_provider import PurchaseResult, SMSProvider
from app.services.providers.fivesim_adapter import FiveSimAdapter
from app.services.providers.predictive_scorer import PredictiveRouterScorer
from app.services.providers.provider_errors import ProviderError
from app.services.providers.pvapins_adapter import COUNTRY_MAP as PVAPINS_COUNTRIES
from app.services.providers.pvapins_adapter import PVAPinsAdapter
from app.services.providers.telnyx_adapter import TelnyxAdapter
from app.services.providers.textverified_adapter import TextVerifiedAdapter
from app.services.purchase_intelligence import PurchaseIntelligenceService

logger = get_logger(__name__)


class ProviderRouter:

    def __init__(self):
        self._textverified: Optional[TextVerifiedAdapter] = None
        self._telnyx: Optional[TelnyxAdapter] = None
        self._fivesim: Optional[FiveSimAdapter] = None
        self._pvapins: Optional[PVAPinsAdapter] = None
        self._settings = get_settings()

    def _get_textverified(self) -> TextVerifiedAdapter:
        if self._textverified is None:
            self._textverified = TextVerifiedAdapter()
        return self._textverified

    def _get_telnyx(self) -> TelnyxAdapter:
        if self._telnyx is None:
            self._telnyx = TelnyxAdapter()
        return self._telnyx

    def _get_fivesim(self) -> FiveSimAdapter:
        if self._fivesim is None:
            self._fivesim = FiveSimAdapter()
        return self._fivesim

    def _get_pvapins(self) -> PVAPinsAdapter:
        if self._pvapins is None:
            self._pvapins = PVAPinsAdapter()
        return self._pvapins

    def _pvapins_covers(self, country: str) -> bool:
        """True if PVApins has a country mapping for this ISO code."""
        return country.upper() in PVAPINS_COUNTRIES

    async def get_provider(
        self,
        db: Session,
        service: str,
        country: str,
        city: Optional[str] = None,
        user_tier: str = "freemium",
        prefer_enterprise: bool = False,
        capability: str = "sms",
    ) -> Tuple[SMSProvider, bool, Optional[str]]:
        """Select provider for a request using Autonomous Predictive Scoring (Phase 12).
        
        Rentals are routed specifically:
        - US Rental -> TextVerified
        - Intl Rental -> 5sim (best effort)
        """
        country_upper = country.upper()
        
        # --- RENTAL ROUTING (V6.0.0) ---
        if capability == "rental":
            if country_upper == "US":
                return self._get_textverified(), False, None
            else:
                return self._get_fivesim(), False, None

        scorer = PredictiveRouterScorer(db)
        # Candidate pool
        candidates = []

        # --- PHASE 12 TIER-BASED PRE-FILTERING ---
        # US is specialized (TextVerified preferred for proximity accuracy)
        if country_upper == "US":
            return self._get_textverified(), bool(city), None

        # Gather enabled and capable providers
        if self._get_textverified().enabled:
            candidates.append(("textverified", self._get_textverified()))

        if self._get_fivesim().enabled:
            candidates.append(("5sim", self._get_fivesim()))

        if self._get_telnyx().enabled:
            # Telnyx is premium/enterprise
            if user_tier in ("pro", "custom") or prefer_enterprise:
                candidates.append(("telnyx", self._get_telnyx()))

        if self._get_pvapins().enabled and self._pvapins_covers(country_upper):
            candidates.append(("pvapins", self._get_pvapins()))

        if not candidates:
            # Fallback to TextVerified if everything else is crippled
            return self._get_textverified(), False, None

        # --- PHASE 12 AUTONOMOUS SCORING ---
        # ... [Scoring logic remains same for SMS]
        scored_candidates = []
        for name, adapter in candidates:
            score = await scorer.calculate_provider_score(
                service=service, country=country_upper, provider_name=name
            )
            scored_candidates.append((score, adapter, name))

        scored_candidates.sort(key=lambda x: x[0], reverse=True)
        winner_score, winner_adapter, winner_name = scored_candidates[0]

        logger.info(
            f"✓ Predictive Router selected {winner_name} (Score: {winner_score:.2f}) "
            f"for {service}/{country_upper}"
        )

        # Handling city metadata
        city_honoured = bool(city) and winner_name != "5sim"
        city_note = None
        if city and winner_name == "5sim":
            city_note = "Precise city filtering temporarily unavailable, assigned country-level number"

        return winner_adapter, city_honoured, city_note

    async def purchase_with_failover(
        self,
        db: Session,
        service: str,
        country: str,
        area_code: Optional[str] = None,
        carrier: Optional[str] = None,
        capability: str = "sms",
        city: Optional[str] = None,
        user_tier: str = "freemium",
        selected_from_alternatives: bool = False,
        original_request: Optional[str] = None,
        duration_hours: Optional[float] = None,
    ) -> PurchaseResult:
        """Purchase with city-aware routing and two-level rerouting."""
        # Resolve area codes for US city requests
        resolved_area_code = area_code
        if country.upper() == "US" and city and not area_code:
            from app.services.providers.city_to_area_code import lookup

            codes = lookup(city)
            if codes:
                resolved_area_code = codes[0]
                logger.info(f"City '{city}' resolved to area codes {codes} for US request")
            else:
                logger.info(f"City '{city}' not in US map, proceeding without area code")

        primary, city_attempted, pre_note = await self.get_provider(
            db, service, country, city, user_tier, capability=capability
        )
        routing_reason = (
            f"country={country}"
            + (f"_city={city}" if city else "")
            + f"_tier={user_tier}"
            + f"_capability={capability}"
        )

        # Build kwargs for provider
        provider_kwargs = {
            "service": service,
            "country": country,
            "area_code": resolved_area_code,
            "carrier": None,
            "capability": capability,
            "city": city if city_attempted else None,
            "duration_hours": duration_hours
        }

        if primary.name == "textverified":
            provider_kwargs["selected_from_alternatives"] = selected_from_alternatives
            provider_kwargs["original_request"] = original_request

        try:
            logger.info(
                f"Purchase attempt: provider={primary.name}, service={service}, "
                f"country={country}, city={city_for_provider}, tier={user_tier}"
            )

            result = await primary.purchase_number(**provider_kwargs)

            # Apply pre-known city note (e.g. PAYG city dropped before API call)
            if pre_note and not result.city_note:
                result.city_honoured = False
                result.city_note = pre_note

            # US city outcome — check if area code matched city
            if country.upper() == "US" and city and resolved_area_code:
                from app.services.providers.city_to_area_code import lookup

                city_codes = lookup(city)
                if city_codes and result.assigned_area_code not in city_codes:
                    result.city_honoured = False
                    result.city_note = f"Requested {city}, assigned nearby area"

            result.routing_reason = routing_reason
            logger.info(
                f"Purchase successful: {result.phone_number} via {primary.name}"
            )
            return result

        except ProviderError as e:
            logger.error(f"Provider {primary.name} error [{e.category}]: {e.internal}")

            # Terminal errors — surface immediately, no rerouting
            if e.is_terminal:
                raise

            # Reroutable errors — try failover provider
            if e.is_reroutable and getattr(
                self._settings, "enable_provider_failover", True
            ):
                secondary = await self._get_failover_provider(
                    db, primary, country, service, user_tier
                )
                if secondary:
                    logger.warning(
                        f"Failing over from {primary.name} to {secondary.name}"
                    )
                    try:
                        # Re-build kwargs for secondary (might be a different provider type)
                        secondary_kwargs = {
                            "service": service,
                            "country": country,
                            "area_code": resolved_area_code,
                            "carrier": None,
                            "capability": capability,
                            "city": city_for_provider,
                        }
                        if secondary.name == "textverified":
                            secondary_kwargs["selected_from_alternatives"] = (
                                selected_from_alternatives
                            )
                            secondary_kwargs["original_request"] = original_request

                        result = await secondary.purchase_number(**secondary_kwargs)
                        if pre_note and not result.city_note:
                            result.city_honoured = False
                            result.city_note = pre_note
                        result.routing_reason = (
                            f"failover {primary.name}->{secondary.name}"
                        )
                        logger.info(
                            f"Failover successful: {result.phone_number} via {secondary.name}"
                        )
                        return result
                    except ProviderError as fe:
                        logger.error(
                            f"Failover provider {secondary.name} also failed [{fe.category}]: {fe.internal}"
                        )
            # All options exhausted
            raise ProviderError(
                "all_providers_failed",
                f"All providers failed for {country}. Last error: {e.internal}",
            )

    async def _get_failover_provider(
        self,
        db: Session,
        failed_provider: SMSProvider,
        country: str,
        service: str,
        user_tier: str,
    ) -> Optional[SMSProvider]:
        """Determine next provider in the chain using Predictive Scoring (Phase 12)."""
        scorer = PredictiveRouterScorer(db)
        country_upper = country.upper()

        # Candidates excluding the failed one
        candidates = []
        if self._get_textverified().enabled and failed_provider.name != "textverified":
            candidates.append(("textverified", self._get_textverified()))
        if self._get_fivesim().enabled and failed_provider.name != "5sim":
            candidates.append(("5sim", self._get_fivesim()))
        if self._get_telnyx().enabled and failed_provider.name != "telnyx":
            if user_tier in ("pro", "custom"):
                candidates.append(("telnyx", self._get_telnyx()))
        if (
            self._get_pvapins().enabled
            and failed_provider.name != "pvapins"
            and self._pvapins_covers(country_upper)
        ):
            candidates.append(("pvapins", self._get_pvapins()))

        if not candidates:
            return None

        # Score remaining candidates
        scored_candidates = []
        for name, adapter in candidates:
            score = await scorer.calculate_provider_score(
                service=service, country=country_upper, provider_name=name
            )
            scored_candidates.append((score, adapter, name))

        scored_candidates.sort(key=lambda x: x[0], reverse=True)

        # We only failover to 'Healthy' enough providers in Phase 12
        if scored_candidates[0][0] < 0.3:  # Threshold for failover viability
            logger.warning(
                f"No viable failover candidates for {country_upper} (best score {scored_candidates[0][0]})"
            )
            return None

        return scored_candidates[0][1]

    async def get_provider_balances(self) -> dict:
        balances = {}
        for name, adapter_fn in [
            ("textverified", self._get_textverified),
            ("telnyx", self._get_telnyx),
            ("5sim", self._get_fivesim),
            ("pvapins", self._get_pvapins),
        ]:
            adapter = adapter_fn()
            if adapter.enabled:
                try:
                    balances[name] = await adapter.get_balance()
                except Exception as e:
                    logger.error(f"Balance check failed for {name}: {e}")
                    balances[name] = 0.0
        return balances

    def get_enabled_providers(self) -> list:
        enabled = []
        if self._get_textverified().enabled:
            enabled.append("textverified")
        if self._get_telnyx().enabled:
            enabled.append("telnyx")
        if self._get_fivesim().enabled:
            enabled.append("5sim")
        if self._get_pvapins().enabled:
            enabled.append("pvapins")
        return enabled
