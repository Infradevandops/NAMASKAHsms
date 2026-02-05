"""Notification dispatcher for real-time notifications."""

from typing import Dict, Any, Optional
from app.core.logging import get_logger
from app.services.notification_service import NotificationService

logger = get_logger(__name__)


class NotificationDispatcher:
    """Handles notification creation and broadcasting."""

    def __init__(self, db):
        self.db = db
        self.notification_service = NotificationService(db)

    def _broadcast_notification(self, user_id: str, notification: Dict[str, Any]):
        """Broadcast notification via WebSocket."""
        try:
            # Import here to avoid circular dependency
            from app.websocket.manager import manager
            import asyncio

            # Send via WebSocket in background
            asyncio.create_task(
                manager.send_personal_message(
                    {"type": "notification", "data": notification}, user_id
                )
            )
            logger.info(
                f"📤 Notification broadcasted to user {user_id}: {notification.get('title', 'No title')}"
            )
        except Exception as e:
            logger.error(f"Failed to broadcast notification via WebSocket: {e}")

    async def notify_verification_started(
        self, 
        user_id: str, 
        verification_id: str, 
        service: str, 
        phone_number: str, 
        cost: float
        ) -> bool:
        """Notify when verification is started."""
        try:
            notification = self.notification_service.create_notification(
                user_id=user_id,
                notification_type="verification_started",
                title="🔄 Verification Started",
                message=f"Started {service} verification for {phone_number} (${cost:.2f})",
                link=f"/verify?id={verification_id}",
            )

            self._broadcast_notification(user_id, notification)
            logger.info(f"Created verification_started notification for {user_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to create verification_started notification: {e}")
        return False

    async def notify_verification_completed(
        self, 
        user_id: str, 
        verification_id: str, 
        service: str, 
        phone_number: str
        ) -> bool:
        """Notify when verification is completed."""
        try:
            notification = self.notification_service.create_notification(
                user_id=user_id,
                notification_type="verification_completed",
                title="✅ Verification Completed",
                message=f"SMS received for {service} verification ({phone_number})",
                link=f"/verify?id={verification_id}",
            )

            self._broadcast_notification(user_id, notification)
            logger.info(f"Created verification_completed notification for {user_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to create verification_completed notification: {e}")
        return False

    async def notify_verification_failed(
        self, 
        user_id: str, 
        verification_id: str, 
        service: str, 
        reason: str
        ) -> bool:
        """Notify when verification fails."""
        try:
            notification = self.notification_service.create_notification(
                user_id=user_id,
                notification_type="verification_failed",
                title="❌ Verification Failed",
                message=f"{service} verification failed: {reason}",
                link=f"/verify?id={verification_id}",
            )

            self._broadcast_notification(user_id, notification)
            logger.info(f"Created verification_failed notification for {user_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to create verification_failed notification: {e}")
        return False

    async def notify_payment_completed(
        self, 
        user_id: str, 
        amount: float, 
        new_balance: float
        ) -> bool:
        """Notify when payment is completed."""
        try:
            notification = self.notification_service.create_notification(
                user_id=user_id,
                notification_type="payment_completed",
                title="💳 Payment Completed",
                message=f"${amount:.2f} added to your account. New balance: ${new_balance:.2f}",
                link="/billing",
            )

            self._broadcast_notification(user_id, notification)
            logger.info(f"Created payment_completed notification for {user_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to create payment_completed notification: {e}")
        return False

    async def notify_verification_timeout(
        self, 
        user_id: str, 
        verification_id: str, 
        service: str, 
        refund_amount: float
        ) -> bool:
        """Notify when verification times out with auto-refund."""
        try:
            notification = self.notification_service.create_notification(
                user_id=user_id,
                notification_type="verification_timeout",
                title="⏰ Verification Timeout - Refunded",
                message=f"{service} verification timed out. ${refund_amount:.2f} refunded to your account.",
                link=f"/verify?id={verification_id}",
            )

            self._broadcast_notification(user_id, notification)
            logger.info(f"Created verification_timeout notification for {user_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to create verification_timeout notification: {e}")
        return False

    async def notify_verification_cancelled(
        self, 
        user_id: str, 
        verification_id: str, 
        service: str, 
        refund_amount: float
        ) -> bool:
        """Notify when verification is cancelled with refund."""
        try:
            notification = self.notification_service.create_notification(
                user_id=user_id,
                notification_type="verification_cancelled",
                title="🚫 Verification Cancelled - Refunded",
                message=f"{service} verification cancelled. ${refund_amount:.2f} refunded to your account.",
                link=f"/verify?id={verification_id}",
            )

            self._broadcast_notification(user_id, notification)
            logger.info(f"Created verification_cancelled notification for {user_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to create verification_cancelled notification: {e}")
        return False

    async def on_refund_completed(
        self, 
        user_id: str, 
        amount: float, 
        reference: str, 
        new_balance: float
        ) -> bool:
        """Notify when any refund is completed."""
        try:
            notification = self.notification_service.create_notification(
                user_id=user_id,
                notification_type="refund_completed",
                title="💰 Refund Completed",
                message=f"${amount:.2f} refunded. New balance: ${new_balance:.2f}",
                link="/billing/history",
            )

            self._broadcast_notification(user_id, notification)
            logger.info(f"Created refund_completed notification for {user_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to create refund_completed notification: {e}")
        return False

    async def on_sms_received(self, verification) -> bool:
        """Notify when SMS is received for verification."""
        try:
            notification = self.notification_service.create_notification(
                user_id=verification.user_id,
                notification_type="sms_received",
                title="📱 SMS Code Received",
                message=f"Verification code received for {verification.service_name}",
                link=f"/verify?id={verification.id}",
            )

            self._broadcast_notification(verification.user_id, notification)
            logger.info(f"Created sms_received notification for {verification.user_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to create sms_received notification: {e}")
        return False
