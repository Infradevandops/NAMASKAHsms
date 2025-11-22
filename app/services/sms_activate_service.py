"""SMS - Activate provider service (placeholder for future integration)."""
from typing import Dict, List, Any
from app.core.logging import get_logger
from app.services.sms_provider_interface import SMSProviderInterface

logger = get_logger(__name__)


class SmsActivateService(SMSProviderInterface):
    """SMS - Activate provider implementation."""

    def __init__(self):
        self.api_key = None  # Will be set from settings
        self.enabled = False
        logger.info("SMS - Activate provider initialized (disabled)")

    async def get_countries(self) -> List[Dict[str, Any]]:
        """Get countries from SMS - Activate."""
        if not self.enabled:
            return []
        # TODO: Implement SMS - Activate API call
        return []

    async def get_services(self, country: str) -> List[Dict[str, Any]]:
        """Get services from SMS - Activate."""
        if not self.enabled:
            return []
        # TODO: Implement SMS - Activate API call
        return []

    async def buy_number(self, country: str, service: str) -> Dict[str, Any]:
        """Buy number from SMS - Activate."""
        if not self.enabled:
            raise Exception("SMS - Activate provider not enabled")
        # TODO: Implement SMS - Activate API call
        return {}

    async def check_sms(self, activation_id: str) -> Dict[str, Any]:
        """Check SMS from SMS - Activate."""
        if not self.enabled:
            return {"status": "error"}
        # TODO: Implement SMS - Activate API call
        return {}

    async def cancel_activation(self, activation_id: str) -> bool:
        """Cancel activation on SMS - Activate."""
        if not self.enabled:
            return False
        # TODO: Implement SMS - Activate API call
        return False
