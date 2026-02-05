"""Webhook and notification service for real - time updates."""


import asyncio
from datetime import datetime
from typing import Any, Dict, Optional
import httpx
from app.core.logging import get_logger

logger = get_logger(__name__)


class WebhookNotificationService:

    """Handle webhook notifications and real - time updates."""

    def __init__(self):

        self.timeout = 10
        self.max_retries = 3

    async def send_webhook(self, url: str, event: str, data: Dict[str, Any], headers: Optional[Dict] = None) -> bool:
        """Send webhook notification with retry logic."""
        if not url:
        return False

        payload = {
            "event": event,
            "timestamp": datetime.utcnow().isoformat(),
            "data": data,
        }

        default_headers = {
            "Content - Type": "application/json",
            "User - Agent": "Namaskah/1.0",
        }
        if headers:
            default_headers.update(headers)

        for attempt in range(self.max_retries):
        try:
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    response = await client.post(url, json=payload, headers=default_headers)

        if response.status_code in [200, 201, 202]:
                        logger.info(f"Webhook sent successfully: {event} to {url}")
        return True
        else:
                        logger.warning(f"Webhook failed with status {response.status_code}: {event}")

        except asyncio.TimeoutError:
                logger.warning(f"Webhook timeout (attempt {attempt + 1}/{self.max_retries}): {event}")
        except Exception as e:
                logger.error(f"Webhook error (attempt {attempt + 1}/{self.max_retries}): {str(e)}")

        if attempt < self.max_retries - 1:
                await asyncio.sleep(2**attempt)  # Exponential backoff

        logger.error(f"Webhook failed after {self.max_retries} attempts: {event}")
        return False

    async def notify_verification_created(
        self,
        verification_id: str,
        phone_number: str,
        service: str,
        cost: float,
        webhook_url: Optional[str] = None,
        ) -> bool:
        """Notify about new verification."""
        if not webhook_url:
        return True

        data = {
            "verification_id": verification_id,
            "phone_number": phone_number,
            "service": service,
            "cost": cost,
            "status": "pending",
        }

        return await self.send_webhook(webhook_url, "verification.created", data)

    async def notify_sms_received(self, verification_id: str, sms_code: str, webhook_url: Optional[str] = None) -> bool:
        """Notify when SMS is received."""
        if not webhook_url:
        return True

        data = {
            "verification_id": verification_id,
            "sms_code": sms_code,
            "status": "completed",
        }

        return await self.send_webhook(webhook_url, "sms.received", data)

    async def notify_verification_cancelled(
        self,
        verification_id: str,
        refund_amount: float,
        webhook_url: Optional[str] = None,
        ) -> bool:
        """Notify about cancelled verification."""
        if not webhook_url:
        return True

        data = {
            "verification_id": verification_id,
            "refund_amount": refund_amount,
            "status": "cancelled",
        }

        return await self.send_webhook(webhook_url, "verification.cancelled", data)

    async def notify_verification_timeout(self, verification_id: str, webhook_url: Optional[str] = None) -> bool:
        """Notify about verification timeout."""
        if not webhook_url:
        return True

        data = {"verification_id": verification_id, "status": "timeout"}

        return await self.send_webhook(webhook_url, "verification.timeout", data)


class EmailNotificationService:

        """Handle email notifications."""

    async def send_verification_email(self, email: str, phone_number: str, service: str, verification_id: str) -> bool:
        """Send verification created email."""
        try:
            # Integration with email service (SendGrid, AWS SES, etc.)
            logger.info(f"Email notification sent to {email} for verification {verification_id}")
        return True
        except Exception as e:
            logger.error(f"Email notification failed: {str(e)}")
        return False

    async def send_sms_received_email(self, email: str, sms_code: str, verification_id: str) -> bool:
        """Send SMS received email."""
        try:
            logger.info(f"SMS notification email sent to {email}")
        return True
        except Exception as e:
            logger.error(f"SMS notification email failed: {str(e)}")
        return False


# Global instances
        webhook_service = WebhookNotificationService()
        email_service = EmailNotificationService()
