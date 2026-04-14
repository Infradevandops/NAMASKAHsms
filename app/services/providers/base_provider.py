"""Base provider interface for SMS verification services."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class PurchaseResult:
    """Unified purchase result from any provider."""

    phone_number: str
    order_id: str  # Provider-specific ID
    cost: float  # Raw provider cost (before markup)
    expires_at: str  # ISO format
    provider: str  # "textverified", "telnyx", "5sim"
    operator: Optional[str] = None
    area_code_matched: bool = True
    carrier_matched: bool = True
    real_carrier: Optional[str] = None
    voip_rejected: bool = False
    fallback_applied: bool = False
    requested_area_code: Optional[str] = None
    assigned_area_code: Optional[str] = None
    same_state_fallback: bool = True
    retry_attempts: int = 0
    routing_reason: str = ""
    tv_object: Any = None  # Only for TextVerified (needed by poll_sms_standard)
    metadata: Dict[str, Any] = field(default_factory=dict)
    # City filtering outcome — always populated, never omitted
    city_honoured: bool = True
    city_note: Optional[str] = None


@dataclass
class MessageResult:
    """Unified SMS/voice message result."""

    text: str
    code: str
    received_at: str  # ISO format
    metadata: Dict[str, Any] = field(default_factory=dict)


class SMSProvider(ABC):
    """Abstract base class for SMS providers.

    Every provider MUST implement these methods. No exceptions.
    This ensures all providers can be used interchangeably.
    """

    @abstractmethod
    async def purchase_number(
        self,
        service: str,
        country: str,
        area_code: Optional[str] = None,
        carrier: Optional[str] = None,
        capability: str = "sms",
    ) -> PurchaseResult:
        """Purchase a phone number for verification.

        Args:
            service: Service name (e.g., "whatsapp", "telegram")
            country: ISO country code (e.g., "US", "GB", "DE")
            area_code: Optional area code filter (US only for most providers)
            carrier: Optional carrier/operator filter
            capability: "sms" or "voice"

        Returns:
            PurchaseResult with phone number and order details

        Raises:
            RuntimeError: If purchase fails
        """
        ...

    @abstractmethod
    async def check_messages(
        self, order_id: str, created_after=None
    ) -> List[MessageResult]:
        """Check for received messages.

        Args:
            order_id: Provider-specific order/activation ID
            created_after: Optional datetime to filter stale messages

        Returns:
            List of MessageResult (empty if no messages yet)
        """
        ...

    @abstractmethod
    async def report_failed(self, order_id: str) -> bool:
        """Report failed verification for refund.

        Args:
            order_id: Provider-specific order/activation ID

        Returns:
            True if report was accepted
        """
        ...

    @abstractmethod
    async def cancel(self, order_id: str) -> bool:
        """Cancel an active verification.

        Args:
            order_id: Provider-specific order/activation ID

        Returns:
            True if cancellation succeeded
        """
        ...

    @abstractmethod
    async def get_balance(self) -> float:
        """Get provider account balance.

        Returns:
            Balance in USD
        """
        ...

    @property
    @abstractmethod
    def name(self) -> str:
        """Provider name for logging and routing."""
        ...

    @property
    @abstractmethod
    def enabled(self) -> bool:
        """Whether this provider is enabled and configured."""
        ...
