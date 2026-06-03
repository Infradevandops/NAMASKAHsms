"""Email notification service for sending notification emails (delegating to consolidated email_service)."""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.logging import get_logger
from app.models.notification import Notification
from app.services.email_service import email_service

logger = get_logger(__name__)


class EmailNotificationService:
    """Service for sending notification emails, delegating to consolidated email_service."""

    def __init__(self, db: Optional[Session] = None):
        settings = get_settings()
        self.resend_api_key = settings.resend_api_key
        self.smtp_host = settings.smtp_host
        self.smtp_port = settings.smtp_port
        self.smtp_user = settings.smtp_user or settings.smtp_username
        self.smtp_password = settings.smtp_password
        self.from_email = settings.from_email or settings.smtp_username
        self.db = db

        if self.resend_api_key:
            self.enabled = True
            self._mode = "resend"
        elif self.smtp_host and self.smtp_user and self.smtp_password:
            self.enabled = True
            self._mode = "smtp"
        else:
            self.enabled = False
            self._mode = None

    async def _send_email(self, to_email: str, subject: str, html_body: str) -> bool:
        # Delegate to the unified service
        return await email_service._send(to_email, subject, html_body)

    async def send_notification_email(
        self,
        user_email: str,
        notification: Notification,
        user_name: Optional[str] = None,
        unsubscribe_token: Optional[str] = None,
    ) -> bool:
        if not self.enabled:
            return False
        try:
            subject = f"[{notification.type.upper()}] {notification.title}"
            html_body = email_service._create_notification_html(
                notification=notification,
                user_name=user_name,
                unsubscribe_token=unsubscribe_token,
            )
            return await self._send_email(
                to_email=user_email, subject=subject, html_body=html_body
            )
        except Exception as e:
            logger.error(f"Failed to send notification email: {str(e)}")
            return False

    async def send_verification_initiated_email(
        self,
        user_email: str,
        service_name: str,
        verification_id: str,
        user_name: Optional[str] = None,
        unsubscribe_token: Optional[str] = None,
    ) -> bool:
        if not self.enabled:
            return False
        try:
            subject = f"Your {service_name} verification has started — Vrenum"
            html_body = email_service._create_verification_initiated_html(
                service_name=service_name,
                verification_id=verification_id,
                user_name=user_name,
                unsubscribe_token=unsubscribe_token,
            )
            return await self._send_email(
                to_email=user_email, subject=subject, html_body=html_body
            )
        except Exception as e:
            logger.error(f"Failed to send verification initiated email: {str(e)}")
            return False

    async def send_verification_completed_email(
        self,
        user_email: str,
        service_name: str,
        verification_id: str,
        cost: float,
        user_name: Optional[str] = None,
        unsubscribe_token: Optional[str] = None,
    ) -> bool:
        if not self.enabled:
            return False
        try:
            subject = f"✅ {service_name} verification complete — Vrenum"
            html_body = email_service._create_verification_completed_html(
                service_name=service_name,
                verification_id=verification_id,
                cost=cost,
                user_name=user_name,
                unsubscribe_token=unsubscribe_token,
            )
            return await self._send_email(
                to_email=user_email, subject=subject, html_body=html_body
            )
        except Exception as e:
            logger.error(f"Failed to send verification completed email: {str(e)}")
            return False

    async def send_low_balance_alert_email(
        self,
        user_email: str,
        current_balance: float,
        threshold: float,
        user_name: Optional[str] = None,
        unsubscribe_token: Optional[str] = None,
    ) -> bool:
        if not self.enabled:
            return False
        try:
            subject = "⚠️ Your Vrenum balance is running low"
            html_body = email_service._create_low_balance_alert_html(
                current_balance=current_balance,
                threshold=threshold,
                user_name=user_name,
                unsubscribe_token=unsubscribe_token,
            )
            return await self._send_email(
                to_email=user_email, subject=subject, html_body=html_body
            )
        except Exception as e:
            logger.error(f"Failed to send low balance alert: {str(e)}")
            return False

    async def send_daily_digest_email(
        self,
        user_email: str,
        notifications: List[Notification],
        user_name: Optional[str] = None,
        unsubscribe_token: Optional[str] = None,
    ) -> bool:
        if not self.enabled:
            return False
        if not notifications:
            logger.info("No notifications to send in digest")
            return False
        try:
            subject = f"📬 Your daily digest — {len(notifications)} update{'s' if len(notifications) != 1 else ''}"
            html_body = email_service._create_daily_digest_html(
                notifications=notifications,
                user_name=user_name,
                unsubscribe_token=unsubscribe_token,
            )
            return await self._send_email(
                to_email=user_email, subject=subject, html_body=html_body
            )
        except Exception as e:
            logger.error(f"Failed to send daily digest: {str(e)}")
            return False

    async def send_weekly_digest_email(
        self,
        user_email: str,
        notifications: List[Notification],
        stats: Dict[str, Any],
        user_name: Optional[str] = None,
        unsubscribe_token: Optional[str] = None,
    ) -> bool:
        if not self.enabled:
            return False
        if not notifications:
            logger.info("No notifications to send in weekly digest")
            return False
        try:
            subject = "📊 Your weekly Vrenum summary"
            html_body = email_service._create_weekly_digest_html(
                notifications=notifications,
                stats=stats,
                user_name=user_name,
                unsubscribe_token=unsubscribe_token,
            )
            return await self._send_email(
                to_email=user_email, subject=subject, html_body=html_body
            )
        except Exception as e:
            logger.error(f"Failed to send weekly digest: {str(e)}")
            return False


email_notification_service = EmailNotificationService()
