"""Telegram notification service"""

import logging
from datetime import datetime
from typing import Any, Dict, Optional

import httpx
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.telegram import TelegramConnection, TelegramForwardingRule
from app.models.verification import Verification

logger = logging.getLogger(__name__)


class TelegramService:
    """Service for sending messages via Telegram Bot API"""

    def __init__(self):
        self.bot_token = getattr(settings, "TELEGRAM_BOT_TOKEN", None)
        self.base_url = (
            f"https://api.telegram.org/bot{self.bot_token}" if self.bot_token else None
        )
        self.rate_limit_delay = 0.034  # ~30 msg/sec limit

    def _get_flag_emoji(self, country_code: str) -> str:
        """Convert country code to flag emoji"""
        if not country_code or len(country_code) != 2:
            return "🌍"

        # Convert to regional indicator symbols
        return "".join(chr(127397 + ord(c)) for c in country_code.upper())

    async def send_message(
        self, chat_id: int, text: str, parse_mode: str = "Markdown"
    ) -> Dict[str, Any]:
        """
        Send a message to a Telegram chat

        Args:
            chat_id: Telegram chat ID
            text: Message text
            parse_mode: Formatting mode (Markdown or HTML)

        Returns:
            API response dict
        """
        if not self.bot_token:
            logger.warning("TELEGRAM_BOT_TOKEN not configured, skipping message")
            return {"ok": False, "error": "Bot token not configured"}

        url = f"{self.base_url}/sendMessage"
        payload = {
            "chat_id": chat_id,
            "text": text,
            "parse_mode": parse_mode,
            "disable_web_page_preview": True,
        }

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(url, json=payload)
                response.raise_for_status()
                return response.json()
        except httpx.HTTPStatusError as e:
            logger.error(
                f"Telegram API error: {e.response.status_code} - {e.response.text}"
            )
            return {"ok": False, "error": str(e)}
        except Exception as e:
            logger.error(f"Failed to send Telegram message: {e}")
            return {"ok": False, "error": str(e)}

    async def send_verification_code(
        self, db: Session, user_id: int, verification: Verification
    ) -> bool:
        """
        Send SMS verification code to user's Telegram

        Args:
            db: Database session
            user_id: User ID
            verification: Verification object with SMS details

        Returns:
            True if sent successfully
        """
        # Get user's Telegram connection
        connection = (
            db.query(TelegramConnection)
            .filter(
                TelegramConnection.user_id == user_id, TelegramConnection.active == True
            )
            .first()
        )

        if not connection:
            logger.debug(f"No active Telegram connection for user {user_id}")
            return False

        # Check forwarding rules
        rules = (
            db.query(TelegramForwardingRule)
            .filter(TelegramForwardingRule.user_id == user_id)
            .first()
        )

        if rules and not rules.forward_all:
            # Check service filter
            if (
                rules.service_filter
                and verification.service not in rules.service_filter
            ):
                logger.debug(f"Service {verification.service} not in filter, skipping")
                return False

            # Check country filter
            if (
                rules.country_filter
                and verification.country not in rules.country_filter
            ):
                logger.debug(f"Country {verification.country} not in filter, skipping")
                return False

        # Format message
        flag = self._get_flag_emoji(verification.country)

        # Calculate time since received
        if verification.updated_at:
            seconds_ago = (datetime.utcnow() - verification.updated_at).total_seconds()
            if seconds_ago < 60:
                time_str = f"{int(seconds_ago)} seconds ago"
            else:
                time_str = f"{int(seconds_ago / 60)} minutes ago"
        else:
            time_str = "just now"

        message = f"""🔔 **SMS Code Received**

Service: {verification.service or 'Unknown'}
Country: {verification.country or 'Unknown'} {flag}
Number: {verification.phone_number or 'N/A'}

Code: **{verification.sms_code or 'Pending'}**

Received: {time_str}
Verification ID: #{verification.id}
"""

        # Send message
        result = await self.send_message(connection.chat_id, message)

        if result.get("ok"):
            # Update last_message_at
            connection.last_message_at = datetime.utcnow()
            db.commit()
            logger.info(f"Sent verification code to Telegram for user {user_id}")
            return True
        else:
            logger.error(f"Failed to send to Telegram: {result.get('error')}")
            return False

    async def send_test_message(self, chat_id: int) -> Dict[str, Any]:
        """Send a test message to verify connection"""
        message = """✅ **Connection Successful!**

Your vrenum.app account is now connected to Telegram.

You'll receive SMS verification codes here instantly.

Use /status to check your connection anytime."""

        return await self.send_message(chat_id, message)

    async def get_bot_info(self) -> Dict[str, Any]:
        """Get bot information"""
        if not self.bot_token:
            return {"ok": False, "error": "Bot token not configured"}

        url = f"{self.base_url}/getMe"

        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(url)
                response.raise_for_status()
                return response.json()
        except Exception as e:
            logger.error(f"Failed to get bot info: {e}")
            return {"ok": False, "error": str(e)}

    def verify_webhook_signature(self, token: str) -> bool:
        """Verify webhook request is from Telegram"""
        # Telegram doesn't use signatures, but we can verify the token
        return token == self.bot_token


# Singleton instance
telegram_service = TelegramService()
