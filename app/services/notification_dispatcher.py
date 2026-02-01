"""Notification dispatcher for event-driven notifications."""


from sqlalchemy.orm import Session
from app.core.logging import get_logger
from app.services.notification_service import NotificationService
from app.websocket.manager import connection_manager
import asyncio

logger = get_logger(__name__)


class NotificationDispatcher:

    """Centralized notification creation for all events."""

def __init__(self, db: Session):

        self.db = db
        self.notification_service = NotificationService(db)

def on_verification_created(self, verification) -> bool:

        """Notification when verification is created."""
try:
            notification = self.notification_service.create_notification(
                user_id=verification.user_id,
                notification_type="verification_initiated",
                title="🚀 Verification Started",
                message=f"Verification for {verification.service_name} initiated. Waiting for SMS...",
                link=f"/verify?id={verification.id}",
            )

            # Broadcast via WebSocket
            self._broadcast_notification(verification.user_id, notification)

            logger.info(f"Created verification_initiated notification for {verification.user_id}")
            return True
except Exception as e:
            logger.error(f"Failed to create verification_initiated notification: {e}")
            return False

def on_sms_received(self, verification) -> bool:

        """Notification when SMS code is received."""
try:
            notification = self.notification_service.create_notification(
                user_id=verification.user_id,
                notification_type="sms_received",
                title="✅ SMS Code Received!",
                message=f"Code: {verification.sms_code} for {verification.service_name}",
                link=f"/verify?id={verification.id}",
            )

            # Broadcast via WebSocket
            self._broadcast_notification(verification.user_id, notification)

            logger.info(f"Created sms_received notification for {verification.user_id}")
            return True
except Exception as e:
            logger.error(f"Failed to create sms_received notification: {e}")
            return False

def on_verification_failed(self, verification, reason: str) -> bool:

        """Notification when verification fails."""
try:
            self.notification_service.create_notification(
                user_id=verification.user_id,
                notification_type="verification_failed",
                title="❌ Verification Failed",
                message=f"Verification for {verification.service_name} failed: {reason}",
                link="/verify",
            )
            logger.info(f"Created verification_failed notification for {verification.user_id}")
            return True
except Exception as e:
            logger.error(f"Failed to create verification_failed notification: {e}")
            return False

def on_credit_deducted(self, user_id: str, amount: float, service: str) -> bool:

        """Notification when credits are deducted."""
try:
            self.notification_service.create_notification(
                user_id=user_id,
                notification_type="credit_deducted",
                title="💳 Credits Deducted",
                message=f"${amount:.2f} deducted for {service}",
                link="/wallet",
            )
            logger.info(f"Created credit_deducted notification for {user_id}")
            return True
except Exception as e:
            logger.error(f"Failed to create credit_deducted notification: {e}")
            return False

def on_refund_issued(self, user_id: str, amount: float, reason: str) -> bool:

        """Notification when refund is issued."""
try:
            self.notification_service.create_notification(
                user_id=user_id,
                notification_type="refund_issued",
                title="💰 Refund Issued",
                message=f"${amount:.2f} refunded: {reason}",
                link="/wallet",
            )
            logger.info(f"Created refund_issued notification for {user_id}")
            return True
except Exception as e:
            logger.error(f"Failed to create refund_issued notification: {e}")
            return False

def on_balance_low(self, user_id: str, current_balance: float) -> bool:

        """Notification when balance is low."""
try:
            self.notification_service.create_notification(
                user_id=user_id,
                notification_type="balance_low",
                title="⚠️ Low Balance",
                message=f"Your balance is ${current_balance:.2f}. Add credits to continue.",
                link="/wallet",
            )
            logger.info(f"Created balance_low notification for {user_id}")
            return True
except Exception as e:
            logger.error(f"Failed to create balance_low notification: {e}")
            return False

def on_refund_initiated(self, user_id: str, amount: float, reason: str, reference: str) -> bool:

        """Notification when refund is initiated."""
try:
            notification = self.notification_service.create_notification(
                user_id=user_id,
                notification_type="refund_initiated",
                title="🔄 Refund Initiated",
                message=f"Refund of ${amount:.2f} initiated. Reason: {reason}. Reference: {reference}",
                link="/wallet",
            )
            self._broadcast_notification(user_id, notification)
            logger.info(f"Created refund_initiated notification for {user_id}")
            return True
except Exception as e:
            logger.error(f"Failed to create refund_initiated notification: {e}")
            return False

def on_refund_processing(self, user_id: str, amount: float, reference: str) -> bool:

        """Notification when refund is being processed."""
try:
            notification = self.notification_service.create_notification(
                user_id=user_id,
                notification_type="refund_processing",
                title="⏳ Refund Processing",
                message=f"Your refund of ${amount:.2f} is being processed. Reference: {reference}",
                link="/wallet",
            )
            self._broadcast_notification(user_id, notification)
            logger.info(f"Created refund_processing notification for {user_id}")
            return True
except Exception as e:
            logger.error(f"Failed to create refund_processing notification: {e}")
            return False

def on_refund_completed(self, user_id: str, amount: float, reference: str, new_balance: float) -> bool:

        """Notification when refund is completed."""
try:
            notification = self.notification_service.create_notification(
                user_id=user_id,
                notification_type="refund_completed",
                title="✅ Refund Completed",
                message=f"${amount:.2f} refunded successfully! New balance: ${new_balance:.2f}. Reference: {reference}",
                link="/wallet",
            )
            self._broadcast_notification(user_id, notification)
            logger.info(f"Created refund_completed notification for {user_id}")
            return True
except Exception as e:
            logger.error(f"Failed to create refund_completed notification: {e}")
            return False

def on_refund_failed(self, user_id: str, amount: float, reason: str, reference: str) -> bool:

        """Notification when refund fails."""
try:
            notification = self.notification_service.create_notification(
                user_id=user_id,
                notification_type="refund_failed",
                title="❌ Refund Failed",
                message=f"Refund of ${amount:.2f} failed: {reason}. Reference: {reference}. Contact support if needed.",
                link="/wallet",
            )
            self._broadcast_notification(user_id, notification)
            logger.info(f"Created refund_failed notification for {user_id}")
            return True
except Exception as e:
            logger.error(f"Failed to create refund_failed notification: {e}")
            return False

def on_refund_cancelled(self, user_id: str, amount: float, reference: str) -> bool:

        """Notification when refund is cancelled."""
try:
            notification = self.notification_service.create_notification(
                user_id=user_id,
                notification_type="refund_cancelled",
                title="🚫 Refund Cancelled",
                message=f"Refund of ${amount:.2f} has been cancelled. Reference: {reference}",
                link="/wallet",
            )
            self._broadcast_notification(user_id, notification)
            logger.info(f"Created refund_cancelled notification for {user_id}")
            return True
except Exception as e:
            logger.error(f"Failed to create refund_cancelled notification: {e}")
            return False

def on_credits_added(self, user_id: str, amount: float, reason: str, new_balance: float) -> bool:

        """Notification when credits are added."""
try:
            notification = self.notification_service.create_notification(
                user_id=user_id,
                notification_type="credits_added",
                title="💰 Credits Added",
                message=f"${amount:.2f} added to your account. Reason: {reason}. New balance: ${new_balance:.2f}",
                link="/wallet",
            )
            self._broadcast_notification(user_id, notification)
            logger.info(f"Created credits_added notification for {user_id}")
            return True
except Exception as e:
            logger.error(f"Failed to create credits_added notification: {e}")
            return False

def on_credits_deducted_enhanced(self, user_id: str, amount: float, reason: str, new_balance: float, verification_id: str = None) -> bool:

        """Enhanced notification when credits are deducted with more details."""
try:
            link = f"/verify?id={verification_id}" if verification_id else "/wallet"
            notification = self.notification_service.create_notification(
                user_id=user_id,
                notification_type="credits_deducted",
                title="💳 Credits Deducted",
                message=f"${amount:.2f} deducted for {reason}. New balance: ${new_balance:.2f}",
                link=link,
            )
            self._broadcast_notification(user_id, notification)
            logger.info(f"Created credits_deducted notification for {user_id}")
            return True
except Exception as e:
            logger.error(f"Failed to create credits_deducted notification: {e}")
            return False

def on_payment_initiated(self, user_id: str, amount: float, reference: str) -> bool:

        """Notification when payment is initiated."""
try:
            notification = self.notification_service.create_notification(
                user_id=user_id,
                notification_type="payment_initiated",
                title="🚀 Payment Started",
                message=f"Payment of ${amount:.2f} initiated. Complete payment to add credits. Reference: {reference}",
                link="/wallet",
            )
            self._broadcast_notification(user_id, notification)
            logger.info(f"Created payment_initiated notification for {user_id}")
            return True
except Exception as e:
            logger.error(f"Failed to create payment_initiated notification: {e}")
            return False

def on_payment_completed(self, user_id: str, amount: float, credits_added: float, reference: str, new_balance: float) -> bool:

        """Notification when payment is completed."""
try:
            notification = self.notification_service.create_notification(
                user_id=user_id,
                notification_type="payment_completed",
                title="✅ Payment Successful",
                message=f"Payment of ${amount:.2f} completed! ${credits_added:.2f} credits added. New balance: ${new_balance:.2f}",
                link="/wallet",
            )
            self._broadcast_notification(user_id, notification)
            logger.info(f"Created payment_completed notification for {user_id}")
            return True
except Exception as e:
            logger.error(f"Failed to create payment_completed notification: {e}")
            return False

def on_payment_failed(self, user_id: str, amount: float, reason: str, reference: str) -> bool:

        """Notification when payment fails."""
try:
            notification = self.notification_service.create_notification(
                user_id=user_id,
                notification_type="payment_failed",
                title="❌ Payment Failed",
                message=f"Payment of ${amount:.2f} failed: {reason}. Reference: {reference}. Try again or contact support.",
                link="/wallet",
            )
            self._broadcast_notification(user_id, notification)
            logger.info(f"Created payment_failed notification for {user_id}")
            return True
except Exception as e:
            logger.error(f"Failed to create payment_failed notification: {e}")
            return False

def _broadcast_notification(self, user_id: str, notification) -> None:

        """Broadcast notification via WebSocket."""
try:

            message = {
                "type": "notification",
                "data": notification.to_dict(),
                "timestamp": notification.created_at.isoformat() if notification.created_at else None
            }

            # Try to broadcast if event loop is running
try:
                loop = asyncio.get_running_loop()
                loop.create_task(connection_manager.broadcast_to_user(user_id, message))
                logger.debug(f"Scheduled broadcast of notification {notification.id} to user {user_id}")
except RuntimeError:
                # No event loop running, skip WebSocket broadcast
                logger.debug(f"No event loop running, skipping WebSocket broadcast for notification {notification.id}")

except Exception as e:
            logger.error(f"Failed to broadcast notification: {e}")