"""TextVerified provider adapter.

Wraps the existing TextVerifiedService to match the SMSProvider interface.
CRITICAL: Do NOT modify TextVerifiedService — it has 18 bug fixes.
"""

from datetime import datetime, timezone
from typing import List, Optional

from app.core.logging import get_logger
from app.services.providers.base_provider import (
    MessageResult,
    PurchaseResult,
    SMSProvider,
)
from app.services.textverified_service import TextVerifiedService

logger = get_logger(__name__)


class TextVerifiedAdapter(SMSProvider):
    """Adapter for TextVerified API.

    Wraps the existing TextVerifiedService to provide the unified
    SMSProvider interface without modifying the battle-tested service.
    """

    def __init__(self):
        self._service = TextVerifiedService()

    @property
    def name(self) -> str:
        return "textverified"

    @property
    def enabled(self) -> bool:
        return self._service.enabled

    async def purchase_number(
        self,
        service: str,
        country: str,
        area_code: Optional[str] = None,
        carrier: Optional[str] = None,
        capability: str = "sms",
        city: Optional[str] = None,
        selected_from_alternatives: bool = False,
        original_request: Optional[str] = None,
    ) -> PurchaseResult:
        """Purchase number from TextVerified."""
        try:
            result = await self._service.create_verification(
                service=service,
                country=country,
                area_code=area_code,
                capability=capability,
                selected_from_alternatives=selected_from_alternatives,
                original_request=original_request,
            )

            return PurchaseResult(
                phone_number=result["phone_number"],
                order_id=result["id"],
                cost=result["cost"],
                expires_at=result["ends_at"],
                provider="textverified",
                operator=result.get("real_carrier"),
                area_code_matched=result.get("area_code_matched", True),
                carrier_matched=result.get("carrier_matched", True),
                real_carrier=result.get("real_carrier"),
                voip_rejected=result.get("voip_rejected", False),
                fallback_applied=result.get("fallback_applied", False),
                requested_area_code=result.get("requested_area_code"),
                assigned_area_code=result.get("assigned_area_code"),
                same_state_fallback=result.get("same_state_fallback", True),
                retry_attempts=result.get("retry_attempts", 0),
                routing_reason="country=US",
                tv_object=result.get("tv_object"),  # CRITICAL: Needed for polling
            )

        except Exception as e:
            logger.error(f"TextVerified purchase failed: {e}")
            raise RuntimeError(f"TextVerified purchase failed: {e}")

    async def check_messages(
        self, order_id: str, created_after=None
    ) -> List[MessageResult]:
        """Check for messages from TextVerified."""
        try:
            result = await self._service.check_sms(
                order_id, created_after=created_after
            )

            if result.get("status") == "COMPLETED" and result.get("messages"):
                messages = result["messages"]
                return [
                    MessageResult(
                        text=msg.get("text", "") if isinstance(msg, dict) else str(msg),
                        code=msg.get("code", "") if isinstance(msg, dict) else "",
                        received_at=datetime.now(timezone.utc).isoformat(),
                    )
                    for msg in messages
                ]

            return []

        except RuntimeError:
            raise  # Already a clean error from TextVerifiedService
        except Exception as e:
            logger.error(f"TextVerified check_messages unexpected error: {e}")
            return []

    async def report_failed(self, order_id: str) -> bool:
        """Report failed verification to TextVerified."""
        return await self._service.report_verification(order_id)

    async def cancel(self, order_id: str) -> bool:
        """Cancel TextVerified verification."""
        return await self._service._cancel_safe(order_id)

    async def get_balance(self) -> float:
        """Get TextVerified balance."""
        result = await self._service.get_balance()
        return result.get("balance", 0.0)
