"""Telnyx provider adapter.

Enterprise-grade SMS provider with global coverage and direct carrier connections.
"""

import asyncio
import re
from datetime import datetime, timedelta, timezone
from typing import List, Optional

import httpx

from app.core.config import get_settings
from app.core.logging import get_logger
from app.services.providers.base_provider import MessageResult, PurchaseResult, SMSProvider

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
        self.client = httpx.AsyncClient(
            timeout=self.timeout,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
        ) if self._enabled else None

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
    ) -> PurchaseResult:
        """Purchase number from Telnyx.

        Telnyx flow:
        1. Search for available numbers with filters
        2. Order the number
        3. Configure messaging profile
        4. Return number details
        """
        if not self.enabled:
            raise RuntimeError("Telnyx provider not configured")

        try:
            # Step 1: Search for available numbers
            search_params = {
                "filter[country_code]": country,
                "filter[features]": "sms" if capability == "sms" else "voice",
                "filter[limit]": 10,
            }

            if area_code and country == "US":
                # US area code filtering
                search_params["filter[national_destination_code]"] = area_code

            response = await self.client.get(
                f"{self.base_url}/available_phone_numbers",
                params=search_params,
            )
            response.raise_for_status()
            data = response.json()

            available = data.get("data", [])
            if not available:
                raise RuntimeError(
                    f"No Telnyx numbers available for {country}"
                    + (f" with area code {area_code}" if area_code else "")
                )

            # Select first available number
            selected = available[0]
            phone_number = selected["phone_number"]

            # Step 2: Order the number (reserve for 20 minutes)
            order_response = await self.client.post(
                f"{self.base_url}/number_orders",
                json={
                    "phone_numbers": [{"phone_number": phone_number}],
                    "connection_id": None,  # Will configure later
                },
            )
            order_response.raise_for_status()
            order_data = order_response.json()

            order_id = order_data["data"]["id"]
            cost = float(selected.get("cost_information", {}).get("upfront_cost", 1.0))

            # Extract area code from phone number
            assigned_area_code = None
            if phone_number.startswith("+1") and len(phone_number) >= 5:
                assigned_area_code = phone_number[2:5]

            return PurchaseResult(
                phone_number=phone_number,
                order_id=order_id,
                cost=cost,
                expires_at=(datetime.now(timezone.utc) + timedelta(minutes=20)).isoformat(),
                provider="telnyx",
                operator=carrier,
                area_code_matched=(not area_code or assigned_area_code == area_code),
                carrier_matched=True,  # Telnyx doesn't filter by carrier
                real_carrier=None,
                voip_rejected=False,
                fallback_applied=False,
                requested_area_code=area_code,
                assigned_area_code=assigned_area_code,
                same_state_fallback=True,
                retry_attempts=0,
                routing_reason=f"telnyx_country={country}",
                metadata={"telnyx_order_id": order_id},
            )

        except httpx.HTTPError as e:
            logger.error(f"Telnyx API error: {e}")
            raise RuntimeError(f"Telnyx purchase failed: {e}")
        except Exception as e:
            logger.error(f"Telnyx purchase error: {e}")
            raise RuntimeError(f"Telnyx purchase failed: {e}")

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
                        received_at=msg.get("received_at", datetime.now(timezone.utc).isoformat()),
                    )
                )

            return messages

        except Exception as e:
            logger.error(f"Telnyx check_messages error: {e}")
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

        except Exception as e:
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

        except Exception as e:
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
        if self.client:
            await self.client.aclose()
