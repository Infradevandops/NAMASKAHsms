"""SMS Activate SMS provider implementation."""
import httpx
from typing import Dict, Any
from app.services.unified_provider import UnifiedSMSProvider

logger = get_logger(__name__)


class SMSActivateProvider(UnifiedSMSProvider):
    """SMS Activate SMS provider implementation."""

    def __init__(self):
        super().__init__("smsactivate", max_retries=3, timeout_seconds=30)
        self.base_url = "https://api.smsactivate.org"
        self.api_key = settings.smsactivate_api_key

    async def _buy_number(self, country: str, service: str) -> Dict[str, Any]:
        """Buy phone number from SMS Activate."""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/getNumber",
                params={
                    "api_key": self.api_key,
                    "service": service,
                    "country": country
                }
            )
            response.raise_for_status()
            return response.json()

    async def _check_sms(self, activation_id: str) -> Dict[str, Any]:
        """Check for SMS from SMS Activate."""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/getStatus",
                params={
                    "api_key": self.api_key,
                    "id": activation_id
                }
            )
            response.raise_for_status()
            return response.json()

    async def _get_balance(self) -> Dict[str, Any]:
        """Get account balance from SMS Activate."""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/getBalance",
                params={"api_key": self.api_key}
            )
            response.raise_for_status()
            return response.json()
