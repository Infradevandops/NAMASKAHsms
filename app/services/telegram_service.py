"""Telegram Bot integration service."""


from typing import Dict
import httpx
from app.core.config import settings

class TelegramService:

    """Telegram Bot API service."""

    def __init__(self):

        self.bot_token = settings.telegram_bot_token
        self.base_url = f"https://api.telegram.org/bot{self.bot_token}"

    async def send_verification_code(self, chat_id: str, code: str) -> Dict:
        """Send verification code via Telegram."""
        url = f"{self.base_url}/sendMessage"

        payload = {
            "chat_id": chat_id,
            "text": f"🔐 Your verification code: {code}",
            "parse_mode": "HTML",
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=payload)
        return response.json()

    async def set_webhook(self, webhook_url: str) -> Dict:
        """Set webhook for receiving updates."""
        url = f"{self.base_url}/setWebhook"

        payload = {"url": webhook_url}

        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=payload)
        return response.json()