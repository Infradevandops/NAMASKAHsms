"""GetSMSCode provider service."""
from typing import Dict, Optional

import httpx

from app.core.config import settings
from app.services.sms_provider_interface import SMSProviderInterface


class GetSMSService(SMSProviderInterface):
    """GetSMSCode provider implementation."""

    def __init__(self):
        self.base_url = "https://api.getsms.online/stubs/handler_api.php"
        self.api_key = settings.GETSMS_API_KEY

    async def get_balance(self) -> float:
        """Get account balance."""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                self.base_url,
                params={"api_key": self.api_key, "action": "getBalance"}
            )
            return float(response.text.split(":")[1])

    async def get_number(self, service: str, country: str = "0") -> Dict:
        """Get phone number for verification."""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                self.base_url,
                params={
                    "api_key": self.api_key,
                    "action": "getNumber",
                    "service": service,
                    "country": country
                }
            )

            if response.text.startswith("ACCESS_NUMBER"):
                parts = response.text.split(":")
                return {
                    "id": parts[1],
                    "number": parts[2],
                    "cost": 0.3
                }
            raise Exception(f"Failed to get number: {response.text}")

    async def get_sms(self, activation_id: str) -> Optional[str]:
        """Get SMS code for activation."""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                self.base_url,
                params={
                    "api_key": self.api_key,
                    "action": "getStatus",
                    "id": activation_id
                }
            )

            if response.text.startswith("STATUS_OK"):
                return response.text.split(":")[1]
            return None

    async def cancel_activation(self, activation_id: str) -> bool:
        """Cancel activation and get refund."""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                self.base_url,
                params={
                    "api_key": self.api_key,
                    "action": "setStatus",
                    "status": "8",
                    "id": activation_id
                }
            )
            return response.text == "ACCESS_CANCEL"
