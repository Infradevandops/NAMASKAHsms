"""Telnyx provider adapter.

Enterprise-grade SMS provider with global coverage and direct carrier connections.
"""

import re
from datetime import datetime, timedelta, timezone
from typing import List, Optional

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


class TelnyxAdapter(SMSProvider):
    """Telnyx API adapter for SMS verification.

    Telnyx is a Tier-1 carrier with:
    - Direct carrier connections in 190+ countries
    - Private IP network
    - Enterprise SLAs
    - Regional number selection
    - Real-time delivery receipts

    API Docs: https://developers.telnyx.com/docs/api/v2/messaging
    """

    def __init__(self):
        settings = get_settings()
        self.api_key = getattr(settings, "telnyx_api_key", None)
        self.base_url = "https://api.telnyx.com/v2"
        self.timeout = getattr(settings, "telnyx_timeout", 30)
        self._enabled = bool(self.api_key)
        # Single shared client — not recreated per request (prevents connection leaks)
        self._client: Optional[httpx.AsyncClient] = None

    def _get_client(self) -> httpx.AsyncClient:
        """Return shared client, creating it once if needed."""
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                timeout=self.timeout,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
            )
        return self._client

    @property
    def client(self) -> httpx.AsyncClient:
        return self._get_client()

    @property
    def name(self) -> str:
        return "telnyx"

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
        city: Optional[str] = None,
    ) -> PurchaseResult:
        """Purchase number from Telnyx with city and area code filtering.

        City retry pattern:
        1. Try with filter[locality]=city
        2. If empty -> retry without city, set city_honoured=False
        3. If still empty -> raise ProviderError(no_inventory_country)
        """
        if not self.enabled:
            raise ProviderError("not_configured", "Telnyx API key not set")

        try:
            # Build search params
            search_params = {
                "filter[country_code]": country,
                "filter[features]": "sms" if capability == "sms" else "voice",
                "filter[limit]": 10,
            }

            # NDC works for any country (not US-only)
            if area_code:
                search_params["filter[national_destination_code]"] = area_code

            # City-level filtering via locality
            if city:
                search_params["filter[locality]"] = city

            response = await self.client.get(
                f"{self.base_url}/available_phone_numbers",
                params=search_params,
            )
            response.raise_for_status()
            available = response.json().get("data", [])

            # Level 1: city retry — drop locality, keep country
            city_honoured = True
            city_note = None
            if not available and city:
                city_honoured = False
                city_note = (
                    f"No numbers available in {city}, country-level number assigned"
                )
                logger.warning(
                    f"Telnyx: no inventory in {city} for {country}, retrying without city"
                )
                del search_params["filter[locality]"]
                response = await self.client.get(
                    f"{self.base_url}/available_phone_numbers",
                    params=search_params,
                )
                response.raise_for_status()
                available = response.json().get("data", [])

            # Level 2: no inventory for country at all
            if not available:
                raise ProviderError(
                    "no_inventory_country",
                    f"No Telnyx numbers available for {country}"
                    + (f" (city={city})" if city else ""),
                )

            selected = available[0]
            phone_number = selected["phone_number"]

            order_response = await self.client.post(
                f"{self.base_url}/number_orders",
                json={
                    "phone_numbers": [{"phone_number": phone_number}],
                    "connection_id": None,
                },
            )
            order_response.raise_for_status()
            order_data = order_response.json()
            order_id = order_data["data"]["id"]
            cost = float(selected.get("cost_information", {}).get("upfront_cost", 1.0))

            assigned_area_code = None
            if phone_number.startswith("+1") and len(phone_number) >= 5:
                assigned_area_code = phone_number[2:5]

            return PurchaseResult(
                phone_number=phone_number,
                order_id=order_id,
                cost=cost,
                expires_at=(
                    datetime.now(timezone.utc) + timedelta(minutes=20)
                ).isoformat(),
                provider="telnyx",
                operator=None,
                area_code_matched=(not area_code or assigned_area_code == area_code),
                carrier_matched=True,
                real_carrier=None,
                voip_rejected=False,
                fallback_applied=not city_honoured,
                requested_area_code=area_code,
                assigned_area_code=assigned_area_code,
                same_state_fallback=True,
                retry_attempts=0,
                routing_reason=f"telnyx_country={country}"
                + (f"_city={city}" if city else ""),
                metadata={"telnyx_order_id": order_id},
                city_honoured=city_honoured,
                city_note=city_note,
            )

        except ProviderError:
            raise
        except httpx.TimeoutException as e:
            logger.error(f"Telnyx purchase timeout for {country}: {e}")
            raise ProviderError("timeout", f"Telnyx timed out for {country}")
        except httpx.ConnectError as e:
            logger.error(f"Telnyx connection error: {e}")
            raise ProviderError("provider_unreachable", f"Telnyx unreachable: {e}")
        except httpx.HTTPStatusError as e:
            logger.error(f"Telnyx HTTP {e.response.status_code} for {country}: {e}")
            raise ProviderError(
                "provider_unreachable", f"Telnyx HTTP {e.response.status_code}"
            )
        except httpx.HTTPError as e:
            logger.error(f"Telnyx API error for {country}: {e}")
            raise ProviderError("provider_unreachable", f"Telnyx API error: {e}")
        except KeyError as e:
            logger.error(f"Telnyx malformed response, missing key: {e}")
            raise ProviderError(
                "malformed_response", f"Telnyx response missing key: {e}"
            )

    async def check_messages(
        self, order_id: str, created_after=None
    ) -> List[MessageResult]:
        """Check for received messages on Telnyx number.

        Telnyx uses webhooks for real-time delivery, but we poll as fallback.
        """
        if not self.enabled:
            return []

        try:
            # Query messages for this number
            # Note: In production, you'd configure a webhook URL and store
            # messages in your DB. This is a polling fallback.
            response = await self.client.get(
                f"{self.base_url}/messages",
                params={
                    "filter[direction]": "inbound",
                    "page[size]": 10,
                },
            )
            response.raise_for_status()
            data = response.json()

            messages = []
            for msg in data.get("data", []):
                text = msg.get("text", "")
                code = self._extract_code(text)

                # Filter by created_after if provided
                if created_after:
                    msg_time = datetime.fromisoformat(
                        msg.get("received_at", "").replace("Z", "+00:00")
                    )
                    if msg_time < created_after:
                        continue

                messages.append(
                    MessageResult(
                        text=text,
                        code=code,
                        received_at=msg.get(
                            "received_at", datetime.now(timezone.utc).isoformat()
                        ),
                    )
                )

            return messages

        except httpx.TimeoutException:
            logger.error(f"Telnyx check_messages timeout for {order_id}")
            return []
        except httpx.ConnectError:
            logger.error(f"Telnyx unreachable during check_messages for {order_id}")
            return []
        except httpx.HTTPError as e:
            logger.error(f"Telnyx check_messages HTTP error: {e}")
            return []

    async def report_failed(self, order_id: str) -> bool:
        """Report failed verification to Telnyx.

        Telnyx doesn't have a "report" endpoint — we cancel the number order.
        """
        return await self.cancel(order_id)

    async def cancel(self, order_id: str) -> bool:
        """Cancel Telnyx number order."""
        if not self.enabled:
            return False

        try:
            response = await self.client.delete(
                f"{self.base_url}/number_orders/{order_id}"
            )
            response.raise_for_status()
            logger.info(f"Cancelled Telnyx order {order_id}")
            return True

        except httpx.TimeoutException:
            logger.warning(f"Telnyx cancel timeout for {order_id}")
            return False
        except httpx.HTTPError as e:
            logger.warning(f"Telnyx cancel failed for {order_id}: {e}")
            return False

    async def get_balance(self) -> float:
        """Get Telnyx account balance."""
        if not self.enabled:
            return 0.0

        try:
            response = await self.client.get(f"{self.base_url}/balance")
            response.raise_for_status()
            data = response.json()
            return float(data.get("data", {}).get("balance", 0.0))

        except httpx.TimeoutException:
            logger.error("Telnyx balance check timed out")
            return 0.0
        except httpx.HTTPError as e:
            logger.error(f"Telnyx balance check failed: {e}")
            return 0.0

    def _extract_code(self, text: str) -> str:
        """Extract verification code from SMS text."""
        if not text:
            return ""

        # Try hyphenated codes first (e.g., 806-185)
        hyphen_match = re.findall(r"\b(\d{3}-\d{3})\b", text)
        if hyphen_match:
            return hyphen_match[-1].replace("-", "")

        # Try plain digit codes (4-8 digits)
        digit_match = re.findall(r"\b(\d{4,8})\b", text)
        if digit_match:
            return digit_match[-1]

        return ""

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self._client:
            await self._client.aclose()
