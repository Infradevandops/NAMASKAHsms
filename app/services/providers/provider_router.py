"""Smart provider router with intelligent routing and failover."""

from typing import Optional

from app.core.config import get_settings
from app.core.logging import get_logger
from app.services.providers.base_provider import PurchaseResult, SMSProvider
from app.services.providers.fivesim_adapter import FiveSimAdapter
from app.services.providers.telnyx_adapter import TelnyxAdapter
from app.services.providers.textverified_adapter import TextVerifiedAdapter

logger = get_logger(__name__)


class ProviderRouter:
    """Smart router for SMS verification providers.

    Routing Strategy:
    1. US requests → TextVerified (proven, area code support)
    2. International → Telnyx (enterprise) or 5sim (cost-effective)
    3. Failover on infrastructure errors only
    4. Feature flags control provider availability
    """

    def __init__(self):
        self._textverified: Optional[TextVerifiedAdapter] = None
        self._telnyx: Optional[TelnyxAdapter] = None
        self._fivesim: Optional[FiveSimAdapter] = None
        self._settings = get_settings()

    def _get_textverified(self) -> TextVerifiedAdapter:
        """Lazy init TextVerified adapter."""
        if self._textverified is None:
            self._textverified = TextVerifiedAdapter()
        return self._textverified

    def _get_telnyx(self) -> TelnyxAdapter:
        """Lazy init Telnyx adapter."""
        if self._telnyx is None:
            self._telnyx = TelnyxAdapter()
        return self._telnyx

    def _get_fivesim(self) -> FiveSimAdapter:
        """Lazy init 5sim adapter."""
        if self._fivesim is None:
            self._fivesim = FiveSimAdapter()
        return self._fivesim

    def get_provider(self, country: str, prefer_enterprise: bool = False) -> SMSProvider:
        """Select provider for a country.

        Routing Rules (in order):
        1. If country == "US" → TextVerified (best US coverage)
        2. If Telnyx enabled and prefer_enterprise → Telnyx
        3. If 5sim enabled → 5sim (cost-effective international)
        4. Fallback → TextVerified

        Args:
            country: ISO country code
            prefer_enterprise: Prefer enterprise provider (Telnyx) over cost-effective (5sim)

        Returns:
            SMSProvider instance
        """
        country_upper = country.upper()

        # Rule 1: US → TextVerified
        if country_upper == "US":
            logger.info("Routing to TextVerified for US request")
            return self._get_textverified()

        # Rule 2: Enterprise preference → Telnyx
        if prefer_enterprise:
            telnyx = self._get_telnyx()
            if telnyx.enabled:
                logger.info(f"Routing to Telnyx for {country} (enterprise preference)")
                return telnyx

        # Rule 3: International → 5sim (cost-effective)
        fivesim = self._get_fivesim()
        if fivesim.enabled:
            logger.info(f"Routing to 5sim for {country} (cost-effective)")
            return fivesim

        # Rule 4: Fallback → Telnyx if available
        telnyx = self._get_telnyx()
        if telnyx.enabled:
            logger.info(f"Routing to Telnyx for {country} (fallback)")
            return telnyx

        # Rule 5: Last resort → TextVerified
        logger.warning(
            f"No international provider available for {country}, falling back to TextVerified"
        )
        return self._get_textverified()

    async def purchase_with_failover(
        self,
        service: str,
        country: str,
        area_code: Optional[str] = None,
        carrier: Optional[str] = None,
        capability: str = "sms",
        prefer_enterprise: bool = False,
    ) -> PurchaseResult:
        """Purchase number with automatic failover.

        CRITICAL: Failover only on infrastructure errors, NOT business errors.
        - Infrastructure errors: network timeout, 500, connection refused
        - Business errors: insufficient balance, no inventory, invalid service

        Args:
            service: Service name
            country: ISO country code
            area_code: Optional area code filter
            carrier: Optional carrier filter
            capability: "sms" or "voice"
            prefer_enterprise: Prefer enterprise provider

        Returns:
            PurchaseResult

        Raises:
            RuntimeError: If all providers fail
        """
        primary = self.get_provider(country, prefer_enterprise)
        routing_reason = f"country={country}"

        try:
            logger.info(
                f"Attempting purchase with {primary.name}: "
                f"service={service}, country={country}, area_code={area_code}, carrier={carrier}"
            )

            result = await primary.purchase_number(
                service=service,
                country=country,
                area_code=area_code,
                carrier=carrier,
                capability=capability,
            )

            result.routing_reason = routing_reason
            logger.info(
                f"✓ Purchase successful with {primary.name}: {result.phone_number}"
            )
            return result

        except Exception as e:
            error_msg = str(e).lower()
            logger.error(f"Primary provider {primary.name} failed: {e}")

            # Check if this is a business error (don't failover)
            business_errors = [
                "insufficient balance",
                "no inventory",
                "service not found",
                "invalid service",
                "not supported",
                "no numbers available",
            ]

            if any(err in error_msg for err in business_errors):
                logger.warning(
                    f"Business error from {primary.name}, not failing over: {error_msg}"
                )
                raise

            # Infrastructure error → try failover
            if not getattr(self._settings, "enable_provider_failover", True):
                logger.warning("Provider failover disabled, not retrying")
                raise

            secondary = self._get_failover_provider(primary, country)
            if secondary is None:
                logger.error("No failover provider available")
                raise

            logger.warning(
                f"Failing over from {primary.name} to {secondary.name} for {country}"
            )

            try:
                result = await secondary.purchase_number(
                    service=service,
                    country=country,
                    area_code=area_code,
                    carrier=carrier,
                    capability=capability,
                )

                result.routing_reason = f"failover from {primary.name} to {secondary.name}"
                logger.info(
                    f"✓ Failover successful with {secondary.name}: {result.phone_number}"
                )
                return result

            except Exception as failover_error:
                logger.error(f"Failover provider {secondary.name} also failed: {failover_error}")
                raise RuntimeError(
                    f"All providers failed. Primary ({primary.name}): {e}. "
                    f"Secondary ({secondary.name}): {failover_error}"
                )

    def _get_failover_provider(
        self, failed_provider: SMSProvider, country: str
    ) -> Optional[SMSProvider]:
        """Get failover provider when primary fails.

        Failover logic:
        - If TextVerified failed → try Telnyx or 5sim
        - If Telnyx failed → try 5sim or TextVerified
        - If 5sim failed → try Telnyx or TextVerified
        """
        failed_name = failed_provider.name

        if failed_name == "textverified":
            # Try Telnyx first, then 5sim
            telnyx = self._get_telnyx()
            if telnyx.enabled:
                return telnyx

            fivesim = self._get_fivesim()
            if fivesim.enabled:
                return fivesim

        elif failed_name == "telnyx":
            # Try 5sim first, then TextVerified
            fivesim = self._get_fivesim()
            if fivesim.enabled:
                return fivesim

            textverified = self._get_textverified()
            if textverified.enabled:
                return textverified

        elif failed_name == "5sim":
            # Try Telnyx first, then TextVerified
            telnyx = self._get_telnyx()
            if telnyx.enabled:
                return telnyx

            textverified = self._get_textverified()
            if textverified.enabled:
                return textverified

        return None

    async def get_provider_balances(self) -> dict:
        """Get balances from all enabled providers."""
        balances = {}

        textverified = self._get_textverified()
        if textverified.enabled:
            try:
                balances["textverified"] = await textverified.get_balance()
            except Exception as e:
                logger.error(f"Failed to get TextVerified balance: {e}")
                balances["textverified"] = 0.0

        telnyx = self._get_telnyx()
        if telnyx.enabled:
            try:
                balances["telnyx"] = await telnyx.get_balance()
            except Exception as e:
                logger.error(f"Failed to get Telnyx balance: {e}")
                balances["telnyx"] = 0.0

        fivesim = self._get_fivesim()
        if fivesim.enabled:
            try:
                balances["5sim"] = await fivesim.get_balance()
            except Exception as e:
                logger.error(f"Failed to get 5sim balance: {e}")
                balances["5sim"] = 0.0

        return balances

    def get_enabled_providers(self) -> list:
        """Get list of enabled provider names."""
        enabled = []

        if self._get_textverified().enabled:
            enabled.append("textverified")

        if self._get_telnyx().enabled:
            enabled.append("telnyx")

        if self._get_fivesim().enabled:
            enabled.append("5sim")

        return enabled
