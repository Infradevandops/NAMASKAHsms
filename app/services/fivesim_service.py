"""5SIM provider service (placeholder for future integration)."""
from typing import Dict, List, Any
from app.core.logging import get_logger

logger = get_logger(__name__)


class FiveSimService(SMSProviderInterface):
    """5SIM provider implementation."""

    def __init__(self):
        self.api_key = None  # Will be set from settings
        self.enabled = False
        logger.info("5SIM provider initialized (disabled)")

    async def get_countries(self) -> List[Dict[str, Any]]:
        """Get countries from 5SIM."""
        if not self.enabled:
            return []
        # TODO: Implement 5SIM API call
        return []

    async def get_services(self, country: str) -> List[Dict[str, Any]]:
        """Get services from 5SIM."""
        if not self.enabled:
            return []
        # TODO: Implement 5SIM API call
        return []

    async def buy_number(self, country: str, service: str) -> Dict[str, Any]:
        """Buy number from 5SIM."""
        if not self.enabled:
            raise Exception("5SIM provider not enabled")
        # TODO: Implement 5SIM API call
        return {}

    async def check_sms(self, activation_id: str) -> Dict[str, Any]:
        """Check SMS from 5SIM."""
        if not self.enabled:
            return {"status": "error"}
        # TODO: Implement 5SIM API call
        return {}

    async def cancel_activation(self, activation_id: str) -> bool:
        """Cancel activation on 5SIM."""
        if not self.enabled:
            return False
        # TODO: Implement 5SIM API call
        return False
