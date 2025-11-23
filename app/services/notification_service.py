"""Notification service for email, SMS, and webhook delivery."""
import logging
import smtplib
from datetime import datetime, timezone
from email.mime.multipart import MIMEMultipart
from typing import Any, Dict, List, Optional

import httpx
from sqlalchemy.orm import Session

from app.core.config import settings

from .base import BaseService

logger = logging.getLogger(__name__)


class NotificationService(BaseService[InAppNotification]):
    """Service for managing notifications and communications."""

    def __init__(self, db: Session):
        super().__init__(InAppNotification, db)

    @staticmethod
    async def send_email(
        to_email: str, subject: str, body: str, is_html: bool = True
    ) -> bool:
        """Send email notification."""
        if not all([settings.smtp_host, settings.smtp_user, settings.smtp_password]):
            logger.warning("Email not configured, skipping: %s", subject)
            return False

        try:
            msg = MIMEMultipart()
            msg["From"] = settings.from_email
            msg["To"] = to_email
            msg["Subject"] = subject

            msg.attach(MIMEText(body, "html" if is_html else "plain"))

            server = smtplib.SMTP(settings.smtp_host, settings.smtp_port)
            server.starttls()
            server.login(settings.smtp_user, settings.smtp_password)
            server.send_message(msg)
            server.quit()

            return True

        except Exception as e:
            logger.error("Email error: %s", e)
            return False

    async def send_webhook(
        self, user_id: str, event_type: str, payload: Dict[str, Any]
    ) -> List[bool]:
        """Send webhook notifications to user's configured endpoints."""
        webhooks = (
            self.db.query(Webhook)
            .filter(Webhook.user_id == user_id, Webhook.is_active.is_(True))
            .all()
        )

        results = []

        for webhook in webhooks:
            try:
                webhook_payload = {
                    "event": event_type,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "data": payload,
                }

                async with httpx.AsyncClient(timeout=5.0) as client:
                    response = await client.post(
                        webhook.url,
                        json=webhook_payload,
                        headers={"Content - Type": "application/json"},
                    )
                    results.append(response.status_code < 400)

            except Exception as e:
                logger.error("Webhook delivery failed for %s: %s", webhook.url, e)
                results.append(False)

        return results

    def create_in_app_notification(
        self,
        user_id: str,
        title: str,
        message: str,
        notification_type: str = "info",
        verification_id: Optional[str] = None,
    ) -> InAppNotification:
        """Create in - app notification for user."""
        notification = InAppNotification(
            user_id=user_id,
            title=title,
            message=message,
            type=notification_type,
            verification_id=verification_id,
        )

        self.db.add(notification)
        self.db.commit()
        self.db.refresh(notification)

        return notification

    def get_user_notifications(
        self, user_id: str, unread_only: bool = False, limit: int = 50
    ) -> List[Dict[str, Any]]:
        """Get user's in - app notifications."""
        query = self.db.query(InAppNotification).filter(
            InAppNotification.user_id == user_id
        )

        if unread_only:
            query = query.filter(InAppNotification.is_read == False)

        notifications = (
            query.order_by(InAppNotification.created_at.desc()).limit(limit).all()
        )

        return [
            {
                "id": n.id,
                "title": n.title,
                "message": n.message,
                "type": n.type,
                "is_read": n.is_read,
                "verification_id": n.verification_id,
                "created_at": n.created_at.isoformat(),
            }
            for n in notifications
        ]

    def mark_notification_read(self, notification_id: str, user_id: str) -> bool:
        """Mark notification as read."""
        notification = (
            self.db.query(InAppNotification)
            .filter(
                InAppNotification.id == notification_id,
                InAppNotification.user_id == user_id,
            )
            .first()
        )

        if notification:
            notification.is_read = True
            self.db.commit()
            return True

        return False

    def mark_all_read(self, user_id: str) -> int:
        """Mark all notifications as read for user."""
        count = (
            self.db.query(InAppNotification)
            .filter(
                InAppNotification.user_id == user_id, InAppNotification.is_read == False
            )
            .update({"is_read": True})
        )

        self.db.commit()
        return count

    def get_notification_preferences(self, user_id: str) -> Dict[str, bool]:
        """Get user's notification preferences."""
        prefs = (
            self.db.query(NotificationPreferences)
            .filter(NotificationPreferences.user_id == user_id)
            .first()
        )

        if not prefs:
            # Create default preferences
            prefs = NotificationPreferences(
                user_id=user_id,
                in_app_notifications=True,
                email_notifications=True,
                receipt_notifications=True,
            )
            self.db.add(prefs)
            self.db.commit()

        return {
            "in_app_notifications": prefs.in_app_notifications,
            "email_notifications": prefs.email_notifications,
            "receipt_notifications": prefs.receipt_notifications,
        }

    def update_notification_preferences(
        self, user_id: str, **preferences
    ) -> Dict[str, bool]:
        """Update user's notification preferences."""
        prefs = (
            self.db.query(NotificationPreferences)
            .filter(NotificationPreferences.user_id == user_id)
            .first()
        )

        if not prefs:
            prefs = NotificationPreferences(user_id=user_id)
            self.db.add(prefs)

        for key, value in preferences.items():
            if hasattr(prefs, key) and value is not None:
                setattr(prefs, key, value)

        self.db.commit()

        return self.get_notification_preferences(user_id)

    async def send_verification_success_notification(
        self, user_id: str, verification_id: str, service_name: str, phone_number: str
    ):
        """Send notification for successful verification."""
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            return

        prefs = self.get_notification_preferences(user_id)

        # In - app notification
        if prefs["in_app_notifications"]:
            self.create_in_app_notification(
                user_id=user_id,
                title="Verification Completed",
                message=f"Your {service_name} verification ({phone_number}) completed successfully!",
                notification_type="success",
                verification_id=verification_id,
            )

        # Email notification
        if prefs["email_notifications"]:
            await self.send_email(
                to_email=user.email,
                subject=f"✅ {service_name.title()} Verification Completed",
                body="<h2>Verification Completed Successfully!</h2>"
                + f"<p>Your {service_name} verification has been completed.</p>"
                + f"<p><strong>Phone Number:</strong> {phone_number}</p>"
                + f"<p><strong>Service:</strong> {service_name}</p>"
                + f"<p><strong>Completed:</strong> {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}</p>"
                + f"<p><a href='{settings.base_url}/app'>View Dashboard</a></p>",
            )

        # Webhook notification
        await self.send_webhook(
            user_id=user_id,
            event_type="verification.completed",
            payload={
                "verification_id": verification_id,
                "service_name": service_name,
                "phone_number": phone_number,
                "status": "completed",
            },
        )

    async def send_low_balance_notification(self, user_id: str, current_balance: float):
        """Send low balance notification."""
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            return

        prefs = self.get_notification_preferences(user_id)

        if prefs["in_app_notifications"]:
            self.create_in_app_notification(
                user_id=user_id,
                title="Low Balance Warning",
                message=f"Your balance is low (N{current_balance:.2f}). Add credits to continue using services.",
                notification_type="warning",
            )

        if prefs["email_notifications"]:
            await self.send_email(
                to_email=user.email,
                subject="⚠️ Low Balance - Namaskah SMS",
                body="<h2>Low Balance Warning</h2>"
                + "<p>Your account balance is running low.</p>"
                + f"<p><strong>Current Balance:</strong> N{current_balance:.2f}</p>"
                + "<p>Add credits to continue using our SMS verification services.</p>"
                + f"<p><a href='{settings.base_url}/app'>Add Credits</a></p>",
            )
