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

from app.core.config import get_settings
from app.core.logging import get_logger
from app.services.providers.base_provider import PurchaseResult, SMSProvider
from app.services.providers.fivesim_adapter import FiveSimAdapter
from app.services.providers.provider_errors import ProviderError
from app.services.providers.pvapins_adapter import COUNTRY_MAP as PVAPINS_COUNTRIES
from app.services.providers.pvapins_adapter import (
    PVAPinsAdapter,
)
from app.services.providers.telnyx_adapter import TelnyxAdapter
from app.services.providers.textverified_adapter import TextVerifiedAdapter

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

    def get_provider(
        self,
        country: str,
        city: Optional[str] = None,
        user_tier: str = "freemium",
        prefer_enterprise: bool = False,
    ) -> Tuple[SMSProvider, bool, Optional[str]]:
        """Select provider for a request.

        Returns (provider, city_will_be_attempted, pre_known_city_note).
        city_will_be_attempted=True means the provider will receive the city filter.
        city_will_be_attempted=False means city is dropped before the API call.
        """
        country_upper = country.upper()

        # US — always TextVerified, city via area code map
        if country_upper == "US":
            logger.info(f"Routing to TextVerified for US request (city={city})")
            return self._get_textverified(), bool(city), None

        # PVApins-covered countries (SE Asia, South Asia, Africa, LATAM)
        # PVApins is primary for these — better inventory than 5sim/Telnyx
        if self._pvapins_covers(country_upper):
            pvapins = self._get_pvapins()
            if pvapins.enabled:
                # City not supported by PVApins — note it but don't block
                city_note = (
                    "City filtering not available for this region" if city else None
                )
                logger.info(f"Routing to PVApins for {country} (regional specialist)")
                return pvapins, False, city_note

        # International + city + Pro/Custom -> Telnyx (precise city)
        if city and user_tier in ("pro", "custom"):
            telnyx = self._get_telnyx()
            if telnyx.enabled:
                logger.info(
                    f"Routing to Telnyx for {country} city={city} (tier={user_tier})"
                )
                return telnyx, True, None
            # Telnyx not available — fall to 5sim, city cannot be honoured
            fivesim = self._get_fivesim()
            if fivesim.enabled:
                note = f"Precise city filtering temporarily unavailable, country-level number assigned"
                logger.warning(
                    f"Telnyx unavailable for {country}, falling to 5sim (city dropped)"
                )
                return fivesim, False, note

        # International + city + PAYG -> 5sim, city dropped
        if city and user_tier == "payg":
            fivesim = self._get_fivesim()
            if fivesim.enabled:
                note = "Precise city filtering requires Pro tier"
                logger.info(f"Routing to 5sim for {country} (PAYG, city dropped)")
                return fivesim, False, note
            # 5sim not available, try Telnyx as bonus
            telnyx = self._get_telnyx()
            if telnyx.enabled:
                logger.info(f"5sim unavailable, routing PAYG to Telnyx for {country}")
                return telnyx, True, None

        # International + no city -> 5sim (cheapest)
        fivesim = self._get_fivesim()
        if fivesim.enabled:
            logger.info(f"Routing to 5sim for {country} (no city)")
            return fivesim, False, None

        # Fallback -> Telnyx
        telnyx = self._get_telnyx()
        if telnyx.enabled:
            logger.info(f"Routing to Telnyx for {country} (5sim unavailable)")
            return telnyx, bool(city), None

        # Last resort -> TextVerified (will likely fail for international but better than nothing)
        logger.warning(
            f"No international provider available for {country}, using TextVerified"
        )
        return self._get_textverified(), False, None

    async def purchase_with_failover(
        self,
        service: str,
        country: str,
        area_code: Optional[str] = None,
        carrier: Optional[str] = None,
        capability: str = "sms",
        city: Optional[str] = None,
        user_tier: str = "freemium",
    ) -> PurchaseResult:
        """Purchase with city-aware routing and two-level rerouting.

        Level 1 (within provider): Telnyx empty for city -> retry without city
        Level 2 (across providers): Provider fails -> try next provider
        Level 3: All providers exhausted -> raise ProviderError(all_providers_failed)
        """
        # Resolve area codes for US city requests
        resolved_area_code = area_code
        if country.upper() == "US" and city and not area_code:
            from app.services.providers.city_to_area_code import lookup

            codes = lookup(city)
            if codes:
                resolved_area_code = codes[
                    0
                ]  # TextVerified proximity chain handles the rest
                logger.info(
                    f"City '{city}' resolved to area codes {codes} for US request"
                )
            else:
                logger.info(
                    f"City '{city}' not in US map, proceeding without area code"
                )

        primary, city_attempted, pre_note = self.get_provider(country, city, user_tier)
        routing_reason = (
            f"country={country}"
            + (f"_city={city}" if city else "")
            + f"_tier={user_tier}"
        )

        # Determine city to pass to provider
        city_for_provider = city if city_attempted else None

        try:
            logger.info(
                f"Purchase attempt: provider={primary.name}, service={service}, "
                f"country={country}, city={city_for_provider}, tier={user_tier}"
            )

            result = await primary.purchase_number(
                service=service,
                country=country,
                area_code=resolved_area_code,
                carrier=None,  # carrier filtering retired
                capability=capability,
                city=city_for_provider,
            )

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
                secondary = self._get_failover_provider(primary, country)
                if secondary:
                    logger.warning(
                        f"Failing over from {primary.name} to {secondary.name}"
                    )
                    try:
                        result = await secondary.purchase_number(
                            service=service,
                            country=country,
                            area_code=resolved_area_code,
                            carrier=None,
                            capability=capability,
                            city=city_for_provider,
                        )
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

    def _get_failover_provider(
        self, failed_provider: SMSProvider, country: str
    ) -> Optional[SMSProvider]:
        """Get next provider to try when primary fails."""
        failed_name = failed_provider.name

        if failed_name == "textverified":
            telnyx = self._get_telnyx()
            if telnyx.enabled:
                return telnyx
            fivesim = self._get_fivesim()
            if fivesim.enabled:
                return fivesim
            pvapins = self._get_pvapins()
            if pvapins.enabled and self._pvapins_covers(country):
                return pvapins

        elif failed_name == "telnyx":
            fivesim = self._get_fivesim()
            if fivesim.enabled:
                return fivesim
            pvapins = self._get_pvapins()
            if pvapins.enabled and self._pvapins_covers(country):
                return pvapins
            textverified = self._get_textverified()
            if textverified.enabled:
                return textverified

        elif failed_name == "5sim":
            pvapins = self._get_pvapins()
            if pvapins.enabled and self._pvapins_covers(country):
                return pvapins
            telnyx = self._get_telnyx()
            if telnyx.enabled:
                return telnyx
            textverified = self._get_textverified()
            if textverified.enabled:
                return textverified

        elif failed_name == "pvapins":
            fivesim = self._get_fivesim()
            if fivesim.enabled:
                return fivesim
            telnyx = self._get_telnyx()
            if telnyx.enabled:
                return telnyx
            textverified = self._get_textverified()
            if textverified.enabled:
                return textverified

        return None

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
