"""Notification dispatcher for event-driven notifications."""

from sqlalchemy.orm import Session

from app.core.logging import get_logger
from app.services.notification_service import NotificationService

logger = get_logger(__name__)


class NotificationDispatcher:
    """Centralized notification creation for all events."""

    def __init__(self, db: Session):
        self.db = db
        self.notification_service = NotificationService(db)

    def on_verification_created(self, verification) -> bool:
        """Notification when verification is created."""
        try:
            self.notification_service.create_notification(
                user_id=verification.user_id,
                notification_type="verification_initiated",
                title="🚀 Verification Started",
                message=f"Verification for {verification.service_name} initiated. Waiting for SMS...",
                link=f"/verify?id={verification.id}",
            )
            logger.info(f"Created verification_initiated notification for {verification.user_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to create verification_initiated notification: {e}")
            return False

    def on_sms_received(self, verification) -> bool:
        """Notification when SMS code is received."""
        try:
            self.notification_service.create_notification(
                user_id=verification.user_id,
                notification_type="sms_received",
                title="✅ SMS Code Received!",
                message=f"Code: {verification.sms_code} for {verification.service_name}",
                link=f"/verify?id={verification.id}",
            )
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

    def on_verification_completed(self, verification) -> bool:
        """Notification when verification is completed."""
        try:
            self.notification_service.create_notification(
                user_id=verification.user_id,
                notification_type="verification_complete",
                title="✅ Verification Complete",
                message=f"Verification for {verification.service_name} completed successfully",
                link=f"/verify?id={verification.id}",
            )
            logger.info(f"Created verification_complete notification for {verification.user_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to create verification_complete notification: {e}")
            return False
