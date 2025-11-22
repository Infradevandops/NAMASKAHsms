"""5SIM provider implementation with unified interface."""
from typing import Dict, Any
from app.core.logging import get_logger
from app.services.provider_base import UnifiedProviderBase, RetryConfig

logger = get_logger(__name__)


class FiveSimProvider(UnifiedProviderBase):
    """5SIM provider with unified interface."""

    def __init__(self):
        retry_config = RetryConfig(
            max_retries=3,
            initial_delay=1.0,
            max_delay=5.0
        )
        super().__init__("5sim", retry_config)
        self.api_key = None
        self.enabled = False
        logger.info("5SIM provider initialized (disabled)")

    async def get_balance(self) -> Dict[str, Any]:
        """Get account balance."""
        if not self.enabled:
            raise Exception("5SIM provider not enabled")

        # TODO: Implement 5SIM API call
        return {
            "balance": 0.0,
            "currency": "USD",
            "provider": "5sim"
        }

    async def buy_number(self, country: str, service: str) -> Dict[str, Any]:
        """Buy number from 5SIM."""
        if not self.enabled:
            raise Exception("5SIM provider not enabled")

        # TODO: Implement 5SIM API call
        return {
            "activation_id": None,
            "phone_number": None,
            "cost": 0.0,
            "provider": "5sim",
            "country": country,
            "service": service
        }

    async def check_sms(self, activation_id: str) -> Dict[str, Any]:
        """Check SMS from 5SIM."""
        if not self.enabled:
            raise Exception("5SIM provider not enabled")

        # TODO: Implement 5SIM API call
        return {
            "sms_code": None,
            "sms_text": None,
            "status": "pending",
            "provider": "5sim"
        }

    async def get_pricing(self, country: str, service: str) -> Dict[str, Any]:
        """Get service pricing."""
        return {
            "cost": 0.50,
            "currency": "USD",
            "provider": "5sim",
            "country": country,
            "service": service
        }

    async def cancel_activation(self, activation_id: str) -> bool:
        """Cancel activation on 5SIM."""
        if not self.enabled:
            return False

        # TODO: Implement 5SIM API call
        return False
