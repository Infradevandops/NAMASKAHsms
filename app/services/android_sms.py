"""Android SMS Gateway integration."""

from typing import Dict, List

import httpx


class AndroidSMSGateway:
    def __init__(self, gateway_url: str, api_key: str):
        self.gateway_url = gateway_url  # Your Android phone IP
        self.api_key = api_key

    async def send_sms(self, phone: str, message: str) -> Dict:
        """Send SMS via Android gateway."""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.gateway_url}/send",
                json={"phone": phone, "message": message, "key": self.api_key},
            )
            return response.json()

    async def get_messages(self, phone: str = None) -> List[Dict]:
        """Get received SMS messages."""
        async with httpx.AsyncClient() as client:
            params = {"key": self.api_key}
            if phone:
                params["phone"] = phone

            response = await client.get(f"{self.gateway_url}/messages", params=params)
            return response.json()

    async def setup_webhook(self, webhook_url: str) -> Dict:
        """Configure webhook for incoming SMS."""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.gateway_url}/webhook",
                json={"url": webhook_url, "key": self.api_key},
            )
            return response.json()
