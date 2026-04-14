"""5sim provider adapter.

International SMS provider with extensive operator coverage in 100+ countries.
"""

import asyncio
import re
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional

import httpx

from app.core.config import get_settings
from app.core.logging import get_logger
from app.services.providers.base_provider import MessageResult, PurchaseResult, SMSProvider
from app.services.providers.provider_errors import ProviderError

logger = get_logger(__name__)


class FiveSimAdapter(SMSProvider):
    """5sim API adapter for SMS verification.

    5sim provides:
    - 100+ countries
    - Deep operator selection (Country -> Service -> Operator hierarchy)
    - Success rate tracking per operator
    - Competitive international pricing

    API Docs: https://5sim.net/docs
    """

    def __init__(self):
        settings = get_settings()
        self.api_key = getattr(settings, "fivesim_api_key", None)
        self.base_url = "https://5sim.net/v1"
        self.timeout = getattr(settings, "fivesim_timeout", 30)
        self._enabled = bool(self.api_key)
        # Single shared client — not recreated per request (prevents connection leaks)
        self._client: Optional[httpx.AsyncClient] = None

        # Cache for country/service/operator mappings
        self._country_cache: Dict[str, str] = {}  # ISO code -> 5sim country name
        self._service_cache: Dict[str, str] = {}  # Service name -> 5sim service name

    def _get_client(self) -> httpx.AsyncClient:
        """Return shared client, creating it once if needed."""
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                timeout=self.timeout,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Accept": "application/json",
                },
            )
        return self._client

    @property
    def client(self) -> httpx.AsyncClient:
        return self._get_client()

    @property
    def name(self) -> str:
        return "5sim"

    @property
    def enabled(self) -> bool:
        return self._enabled

    async def purchase_number(
        self,
        service: str,
        country: str,
        area_code: Optional[str] = None,
        carrier: Optional[str] = None,
        capability: str = "sms",
    ) -> PurchaseResult:
        """Purchase number from 5sim.

        5sim flow:
        1. Get available products for country/service/operator
        2. Purchase number
        3. Poll for SMS
        """
        if not self.enabled:
            raise ProviderError("not_configured", "5sim API key not set")

        try:
            country_name = await self._map_country(country)
            if not country_name:
                raise ProviderError("unsupported_country", f"5sim: no mapping for {country}")

            service_name = await self._map_service(service)
            if not service_name:
                raise ProviderError("unsupported_service", f"5sim: no mapping for {service}")

            # Get best operator if not specified
            operator = carrier or await self._get_best_operator(
                country_name, service_name
            )

            # Purchase number
            purchase_url = f"{self.base_url}/user/buy/activation/{country_name}/{operator}/{service_name}"
            response = await self.client.get(purchase_url)
            response.raise_for_status()
            data = response.json()

            order_id = str(data.get("id"))
            phone_number = data.get("phone")
            cost = float(data.get("price", 0.0))

            if not phone_number:
                raise ProviderError("malformed_response", "5sim: no phone number in response")

            return PurchaseResult(
                phone_number=f"+{phone_number}",
                order_id=order_id,
                cost=cost,
                expires_at=(datetime.now(timezone.utc) + timedelta(minutes=20)).isoformat(),
                provider="5sim",
                operator=operator,
                area_code_matched=True,
                carrier_matched=bool(operator),
                real_carrier=operator,
                voip_rejected=False,
                fallback_applied=False,
                requested_area_code=None,
                assigned_area_code=None,
                same_state_fallback=True,
                retry_attempts=0,
                routing_reason=f"5sim_country={country}_operator={operator}",
                metadata={"5sim_id": order_id, "country": country_name, "operator": operator},
                city_honoured=True,  # 5sim never receives city — nothing to dishonour
                city_note=None,
            )

        except ProviderError:
            raise
        except httpx.TimeoutException as e:
            logger.error(f"5sim purchase timeout for {country}: {e}")
            raise ProviderError("timeout", f"5sim timed out for {country}")
        except httpx.ConnectError as e:
            logger.error(f"5sim connection error: {e}")
            raise ProviderError("provider_unreachable", f"5sim unreachable: {e}")
        except httpx.HTTPStatusError as e:
            logger.error(f"5sim HTTP {e.response.status_code} for {country}: {e}")
            raise ProviderError("no_inventory_country", f"5sim HTTP {e.response.status_code} for {country}")
        except httpx.HTTPError as e:
            logger.error(f"5sim API error for {country}: {e}")
            raise ProviderError("provider_unreachable", f"5sim API error: {e}")
        except KeyError as e:
            logger.error(f"5sim malformed response, missing key: {e}")
            raise ProviderError("malformed_response", f"5sim response missing key: {e}")

    async def check_messages(
        self, order_id: str, created_after=None
    ) -> List[MessageResult]:
        """Check for received messages on 5sim number."""
        if not self.enabled:
            return []

        try:
            response = await self.client.get(
                f"{self.base_url}/user/check/{order_id}"
            )
            response.raise_for_status()
            data = response.json()

            # 5sim status: PENDING, RECEIVED, CANCELED, TIMEOUT
            status = data.get("status")
            if status == "RECEIVED":
                sms_list = data.get("sms", [])
                if sms_list:
                    messages = []
                    for sms in sms_list:
                        text = sms.get("text", "")
                        code = sms.get("code", "") or self._extract_code(text)
                        received_at = sms.get("created_at", datetime.now(timezone.utc).isoformat())

                        messages.append(
                            MessageResult(
                                text=text,
                                code=code,
                                received_at=received_at,
                            )
                        )
                    return messages

            return []

        except httpx.TimeoutException:
            logger.error(f"5sim check_messages timeout for {order_id}")
            return []
        except httpx.ConnectError:
            logger.error(f"5sim unreachable during check_messages for {order_id}")
            return []
        except httpx.HTTPError as e:
            logger.error(f"5sim check_messages HTTP error: {e}")
            return []

    async def report_failed(self, order_id: str) -> bool:
        """Report failed verification to 5sim."""
        if not self.enabled:
            return False

        try:
            # 5sim: Cancel activation to get refund
            response = await self.client.get(
                f"{self.base_url}/user/cancel/{order_id}"
            )
            response.raise_for_status()
            logger.info(f"Reported failed 5sim activation {order_id}")
            return True

        except httpx.TimeoutException:
            logger.warning(f"5sim report_failed timeout for {order_id}")
            return False
        except httpx.HTTPError as e:
            logger.warning(f"5sim report_failed error for {order_id}: {e}")
            return False

    async def cancel(self, order_id: str) -> bool:
        """Cancel 5sim activation."""
        return await self.report_failed(order_id)

    async def get_balance(self) -> float:
        """Get 5sim account balance."""
        if not self.enabled:
            return 0.0

        try:
            response = await self.client.get(f"{self.base_url}/user/profile")
            response.raise_for_status()
            data = response.json()
            return float(data.get("balance", 0.0))

        except httpx.TimeoutException:
            logger.error("5sim balance check timed out")
            return 0.0
        except httpx.HTTPError as e:
            logger.error(f"5sim balance check failed: {e}")
            return 0.0

    async def _map_country(self, iso_code: str) -> Optional[str]:
        """Map ISO country code to 5sim country name."""
        if iso_code in self._country_cache:
            return self._country_cache[iso_code]

        # Fetch country list from 5sim
        try:
            response = await self.client.get(f"{self.base_url}/guest/countries")
            response.raise_for_status()
            countries = response.json()

            # Build mapping
            for country_name, country_data in countries.items():
                # 5sim uses country names like "russia", "unitedkingdom"
                # Try to match ISO codes
                if country_name.lower() == iso_code.lower():
                    self._country_cache[iso_code] = country_name
                    return country_name

            # Fallback: common mappings
            mapping = {
                "US": "usa",
                "GB": "unitedkingdom",
                "DE": "germany",
                "FR": "france",
                "IN": "india",
                "CA": "canada",
                "RU": "russia",
                "CN": "china",
            }
            if iso_code in mapping:
                self._country_cache[iso_code] = mapping[iso_code]
                return mapping[iso_code]

            return None

        except httpx.TimeoutException:
            logger.error(f"5sim country mapping timed out for {iso_code}")
            return None
        except httpx.HTTPError as e:
            logger.error(f"5sim country mapping failed: {e}")
            return None

    async def _map_service(self, service: str) -> Optional[str]:
        """Map service name to 5sim service name."""
        if service in self._service_cache:
            return self._service_cache[service]

        # 5sim uses lowercase service names
        service_lower = service.lower()

        # Common mappings
        mapping = {
            "whatsapp": "whatsapp",
            "telegram": "telegram",
            "google": "google",
            "facebook": "facebook",
            "instagram": "instagram",
            "twitter": "twitter",
            "tiktok": "tiktok",
            "discord": "discord",
            "uber": "uber",
            "amazon": "amazon",
        }

        if service_lower in mapping:
            self._service_cache[service] = mapping[service_lower]
            return mapping[service_lower]

        # Fallback: use as-is
        self._service_cache[service] = service_lower
        return service_lower

    async def _get_best_operator(self, country: str, service: str) -> str:
        """Get best operator for country/service based on availability."""
        try:
            # Get product prices (includes operator info)
            response = await self.client.get(
                f"{self.base_url}/guest/products/{country}/{service}"
            )
            response.raise_for_status()
            data = response.json()

            # Find operator with lowest price and availability
            best_operator = None
            best_price = float("inf")

            for operator, operator_data in data.items():
                if isinstance(operator_data, dict):
                    price = operator_data.get("cost", float("inf"))
                    count = operator_data.get("count", 0)

                    if count > 0 and price < best_price:
                        best_operator = operator
                        best_price = price

            if best_operator:
                logger.info(
                    f"5sim auto-selected operator {best_operator} for {country}/{service} "
                    f"(price: ${best_price:.2f})"
                )
                return best_operator

            # Fallback: return "any"
            return "any"

        except httpx.TimeoutException:
            logger.warning(f"5sim operator selection timed out, using 'any'")
            return "any"
        except httpx.HTTPError as e:
            logger.warning(f"5sim operator selection failed: {e}, using 'any'")
            return "any"

    def _extract_code(self, text: str) -> str:
        """Extract verification code from SMS text."""
        if not text:
            return ""

        # Try hyphenated codes first
        hyphen_match = re.findall(r"\b(\d{3}-\d{3})\b", text)
        if hyphen_match:
            return hyphen_match[-1].replace("-", "")

        # Try plain digit codes
        digit_match = re.findall(r"\b(\d{4,8})\b", text)
        if digit_match:
            return digit_match[-1]

        return ""

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.client:
            await self.client.aclose()
