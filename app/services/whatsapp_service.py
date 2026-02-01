"""WhatsApp Business API integration."""


from typing import Dict, Optional
import httpx
from app.core.config import settings

class WhatsAppService:

    """WhatsApp Business API service."""

def __init__(self):

        self.base_url = "https://graph.facebook.com/v18.0"
        self.phone_number_id = settings.whatsapp_phone_number_id
        self.access_token = settings.whatsapp_access_token

    async def send_verification_code(self, phone_number: str) -> Dict:
        """Send WhatsApp verification code."""
        url = f"{self.base_url}/{self.phone_number_id}/messages"

        payload = {
            "messaging_product": "whatsapp",
            "to": phone_number,
            "type": "template",
            "template": {
                "name": "verification_code",
                "language": {"code": "en"},
                "components": [
                    {
                        "type": "body",
                        "parameters": [{"type": "text", "text": "123456"}],  # Generated code
                    }
                ],
            },
        }

        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content - Type": "application/json",
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=payload, headers=headers)
            return response.json()

    async def verify_webhook(self, token: str, challenge: str) -> Optional[str]:
        """Verify WhatsApp webhook."""
        verify_token = settings.whatsapp_verify_token
if token == verify_token:
            return challenge
        return None