"""PVApins provider adapter.

Specialises in Southeast Asia and regions with thin coverage from other providers.
Malaysia, Indonesia, Philippines, Vietnam, Thailand, and more.

API: https://api.pvapins.com/user/api/
- get_number.php  -> activation (one-time)
- rent.php        -> rental
- Rate limit: 5 numbers per minute

Response codes:
    100 -> success, data = phone number
    200 -> unavailable, data = error message
    other -> unexpected error
"""

import re
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional

import httpx

from app.core.config import get_settings
from app.core.logging import get_logger
from app.services.providers.base_provider import (
    MessageResult,
    PurchaseResult,
    SMSProvider,
)
from app.services.providers.provider_errors import ProviderError

logger = get_logger(__name__)

# ISO country code -> PVApins country name
COUNTRY_MAP: Dict[str, str] = {
    "MY": "malaysia",
    "ID": "indonesia",
    "PH": "philippines",
    "VN": "vietnam",
    "TH": "thailand",
    "IN": "india",
    "PK": "pakistan",
    "BD": "bangladesh",
    "NG": "nigeria",
    "GH": "ghana",
    "KE": "kenya",
    "EG": "egypt",
    "BR": "brazil",
    "MX": "mexico",
    "CO": "colombia",
    "RU": "russia",
    "UA": "ukraine",
    "KZ": "kazakhstan",
    "CN": "china",
    "KR": "southkorea",
    "JP": "japan",
    "GB": "unitedkingdom",
    "DE": "germany",
    "FR": "france",
    "IT": "italy",
    "ES": "spain",
    "PL": "poland",
    "CA": "canada",
    "AU": "australia",
}

# Services that PVApins supports (lowercase)
SUPPORTED_SERVICES = {
    "google",
    "whatsapp",
    "telegram",
    "facebook",
    "instagram",
    "twitter",
    "tiktok",
    "discord",
    "uber",
    "amazon",
    "netflix",
    "spotify",
    "snapchat",
    "linkedin",
    "microsoft",
    "paypal",
}


class PVAPinsAdapter(SMSProvider):
    """PVApins SMS verification adapter.

    Best for: Southeast Asia, South Asia, Africa, Latin America.
    Activation and rental modes supported.
    """

    BASE_URL = "https://api.pvapins.com/user/api"

    def __init__(self):
        settings = get_settings()
        self.api_key = getattr(settings, "pvapins_api_key", None)
        self.timeout = getattr(settings, "pvapins_timeout", 30)
        self._enabled = bool(self.api_key)
        self._client: Optional[httpx.AsyncClient] = None

    def _get_client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(timeout=self.timeout)
        return self._client

    @property
    def name(self) -> str:
        return "pvapins"

    @property
    def enabled(self) -> bool:
        return self._enabled

    def _map_country(self, iso_code: str) -> Optional[str]:
        """Map ISO country code to PVApins country name."""
        return COUNTRY_MAP.get(iso_code.upper())

    def _map_service(self, service: str) -> str:
        """Map service name to PVApins app name."""
        s = service.lower().strip()
        return s if s in SUPPORTED_SERVICES else s

    async def purchase_number(
        self,
        service: str,
        country: str,
        area_code: Optional[str] = None,
        carrier: Optional[str] = None,
        capability: str = "sms",
        city: Optional[str] = None,
    ) -> PurchaseResult:
        """Purchase activation number from PVApins.

        PVApins does not support area code, carrier, or city filtering.
        Country-level only. City is silently not sent (not an error).
        """
        if not self.enabled:
            raise ProviderError("not_configured", "PVApins API key not set")

        country_name = self._map_country(country)
        if not country_name:
            raise ProviderError(
                "unsupported_country",
                f"PVApins: no mapping for country {country}",
            )

        app_name = self._map_service(service)

        try:
            response = await self._get_client().get(
                f"{self.BASE_URL}/get_number.php",
                params={
                    "customer": self.api_key,
                    "app": app_name,
                    "country": country_name,
                },
            )
            response.raise_for_status()
            data = response.json()

            code = data.get("code")
            number = data.get("data", "")

            if code == 200 or "unavailable" in str(number).lower():
                raise ProviderError(
                    "no_inventory_country",
                    f"PVApins: no numbers available for {country}/{service}",
                )

            if code != 100 or not number:
                raise ProviderError(
                    "malformed_response",
                    f"PVApins: unexpected response code={code} data={number}",
                )

            # PVApins returns number without + prefix
            phone = f"+{number}" if not number.startswith("+") else number

            return PurchaseResult(
                phone_number=phone,
                order_id=number,  # raw number is the order ID for reuse
                cost=0.0,  # PVApins deducts from account balance, no per-call cost in response
                expires_at=(
                    datetime.now(timezone.utc) + timedelta(minutes=20)
                ).isoformat(),
                provider="pvapins",
                operator=None,
                area_code_matched=True,
                carrier_matched=True,
                real_carrier=None,
                voip_rejected=False,
                fallback_applied=False,
                requested_area_code=None,
                assigned_area_code=None,
                same_state_fallback=True,
                retry_attempts=0,
                routing_reason=f"pvapins_country={country}",
                metadata={
                    "pvapins_number": number,
                    "country": country_name,
                    "app": app_name,
                },
                city_honoured=False if city else True,
                city_note=(
                    "City filtering not supported for this region" if city else None
                ),
            )

        except ProviderError:
            raise
        except httpx.TimeoutException as e:
            logger.error(f"PVApins timeout for {country}/{service}: {e}")
            raise ProviderError("timeout", f"PVApins timed out for {country}")
        except httpx.ConnectError as e:
            logger.error(f"PVApins connection error: {e}")
            raise ProviderError("provider_unreachable", f"PVApins unreachable: {e}")
        except httpx.HTTPStatusError as e:
            logger.error(f"PVApins HTTP {e.response.status_code}: {e}")
            raise ProviderError(
                "provider_unreachable", f"PVApins HTTP {e.response.status_code}"
            )
        except (ValueError, KeyError) as e:
            logger.error(f"PVApins malformed response: {e}")
            raise ProviderError("malformed_response", f"PVApins bad response: {e}")

    async def check_messages(
        self, order_id: str, created_after=None
    ) -> List[MessageResult]:
        """Check for received SMS on PVApins number.

        PVApins does not have a dedicated SMS check endpoint in the provided docs.
        Messages are delivered via the activation flow — the number is polled
        by checking if the service sent a code to it.

        For now returns empty list — polling is handled by the platform's
        existing SMS polling service which checks the number directly.
        """
        # PVApins API does not expose an SMS retrieval endpoint in the docs provided.
        # The platform's existing polling service handles code retrieval.
        return []

    async def report_failed(self, order_id: str) -> bool:
        """Report failed verification to PVApins.

        PVApins does not have a report/refund endpoint in the provided docs.
        Returns False — platform AutoRefundService handles the refund fallback.
        """
        logger.info(
            f"PVApins: no report endpoint available for {order_id}, platform refund will handle"
        )
        return False

    async def cancel(self, order_id: str) -> bool:
        """Cancel PVApins activation.

        No cancel endpoint in provided docs. Returns False gracefully.
        """
        logger.info(f"PVApins: no cancel endpoint available for {order_id}")
        return False

    async def get_balance(self) -> float:
        """Get PVApins account balance.

        No balance endpoint in provided docs. Returns 0.0 — balance monitor
        will log a warning but not disable the provider.
        """
        logger.debug("PVApins: no balance endpoint in API docs, returning 0.0")
        return 0.0

    def _extract_code(self, text: str) -> str:
        if not text:
            return ""
        hyphen = re.findall(r"\b(\d{3}-\d{3})\b", text)
        if hyphen:
            return hyphen[-1].replace("-", "")
        digits = re.findall(r"\b(\d{4,8})\b", text)
        return digits[-1] if digits else ""

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self._client:
            await self._client.aclose()
