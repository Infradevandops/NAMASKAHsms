"""Notification dispatcher for real-time notifications."""

from typing import Any, Dict, Optional

from app.core.logging import get_logger
from app.services.notification_service import NotificationService

logger = get_logger(__name__)


class NotificationDispatcher:
    """Handles notification creation and broadcasting."""

    def __init__(self, db):
        self.db = db
        self.notification_service = NotificationService(db)

    def _broadcast_notification(self, user_id: str, notification):
        """Broadcast notification via WebSocket."""
        try:
            import asyncio

            from app.websocket.manager import manager

            # Serialize ORM object to dict before sending over WebSocket
            payload = (
                notification.to_dict()
                if hasattr(notification, "to_dict")
                else notification
            )

            asyncio.create_task(
                manager.send_personal_message(
                    {"type": "notification", "data": payload}, user_id
                )
            )
            logger.info(
                f"Notification broadcasted to user {user_id}: {payload.get('title', 'No title')}"
            )
        except Exception as e:
            logger.error(f"Failed to broadcast notification via WebSocket: {e}")

    async def notify_verification_started(
        self,
        user_id: str,
        verification_id: str,
        service: str,
        phone_number: str,
        cost: float,
    ) -> bool:
        """Notify when verification is started."""
        try:
            notification = self.notification_service.create_notification(
                user_id=user_id,
                notification_type="verification_started",
                title="Verification Started",
                message=f"Started {service} verification for {phone_number} (${cost:.2f})",
            )

            self._broadcast_notification(user_id, notification)
            logger.info(f"Created verification_started notification for {user_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to create verification_started notification: {e}")
        return False

    async def notify_verification_completed(
        self, user_id: str, verification_id: str, service: str, phone_number: str
    ) -> bool:
        """Notify when verification is completed."""
        try:
            notification = self.notification_service.create_notification(
                user_id=user_id,
                notification_type="verification_completed",
                title="Verification Completed",
                message=f"SMS received for {service} verification ({phone_number})",
            )

            self._broadcast_notification(user_id, notification)
            logger.info(f"Created verification_completed notification for {user_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to create verification_completed notification: {e}")
        return False

    async def notify_verification_failed(
        self, user_id: str, verification_id: str, service: str, reason: str
    ) -> bool:
        """Notify when verification fails."""
        try:
            notification = self.notification_service.create_notification(
                user_id=user_id,
                notification_type="verification_failed",
                title="Verification Failed",
                message=f"{service} verification failed: {reason}",
            )

            self._broadcast_notification(user_id, notification)
            logger.info(f"Created verification_failed notification for {user_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to create verification_failed notification: {e}")
        return False

    async def notify_payment_completed(
        self, user_id: str, amount: float, new_balance: float
    ) -> bool:
        """Notify when payment is completed."""
        try:
            notification = self.notification_service.create_notification(
                user_id=user_id,
                notification_type="payment_completed",
                title="Payment Completed",
                message=f"${amount:.2f} added to your account. New balance: ${new_balance:.2f}",
            )

            self._broadcast_notification(user_id, notification)
            logger.info(f"Created payment_completed notification for {user_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to create payment_completed notification: {e}")
        return False

    async def notify_verification_timeout(
        self, user_id: str, verification_id: str, service: str, refund_amount: float
    ) -> bool:
        """Notify when verification times out with auto-refund."""
        try:
            notification = self.notification_service.create_notification(
                user_id=user_id,
                notification_type="verification_timeout",
                title="Verification Timeout - Refunded",
                message=f"{service} verification timed out. ${refund_amount:.2f} refunded to your account.",
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
        refund_amount: float,
        new_balance: float = None,
    ) -> bool:
        """Notify when verification is cancelled with refund."""
        try:
            balance_str = (
                f" New balance: ${new_balance:.2f}" if new_balance is not None else ""
            )
            notification = self.notification_service.create_notification(
                user_id=user_id,
                notification_type="verification_cancelled",
                title="Verification Cancelled",
                message=f"${refund_amount:.2f} refunded for {service}.{balance_str}",
            )

            self._broadcast_notification(user_id, notification)
            logger.info(f"Created verification_cancelled notification for {user_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to create verification_cancelled notification: {e}")
        return False

    async def on_refund_completed(
        self, user_id: str, amount: float, reference: str, new_balance: float
    ) -> bool:
        """Notify when any refund is completed."""
        try:
            notification = self.notification_service.create_notification(
                user_id=user_id,
                notification_type="refund_completed",
                title="Refund Completed",
                message=f"${amount:.2f} refunded. New balance: ${new_balance:.2f}",
            )

            self._broadcast_notification(user_id, notification)
            logger.info(f"Created refund_completed notification for {user_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to create refund_completed notification: {e}")
        return False

    async def notify_balance_deducted(
        self, user_id: str, amount: float, service: str, new_balance: float
    ) -> bool:
        """Notify when credits are deducted for a verification purchase."""
        try:
            notification = self.notification_service.create_notification(
                user_id=user_id,
                notification_type="balance_update",
                title="Balance Updated",
                message=f"${amount:.2f} charged for {service} - New balance: ${new_balance:.2f}",
            )
            self._broadcast_notification(user_id, notification)
            logger.info(f"Created balance_update notification for {user_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to create balance_update notification: {e}")
        return False

    async def notify_area_code_fallback(
        self,
        user_id: str,
        verification_id: str,
        service: str,
        requested_area_code: str,
        assigned_area_code: str,
        same_state: bool,
    ) -> bool:
        """Notify when area code fallback is applied during auto-selection."""
        try:
            if same_state:
                title = "Area Code Substituted"
                message = (
                    f"{service}: requested {requested_area_code}, "
                    f"assigned {assigned_area_code} (same state)"
                )
                ntype = "area_code_fallback"
            else:
                title = "⚠️ Cross-State Area Code"
                message = (
                    f"{service}: requested {requested_area_code}, "
                    f"assigned {assigned_area_code} (different state)"
                )
                ntype = "area_code_cross_state"

            notification = self.notification_service.create_notification(
                user_id=user_id,
                notification_type=ntype,
                title=title,
                message=message,
            )
            self._broadcast_notification(user_id, notification)
            logger.info(
                f"Created {ntype} notification for {user_id}: "
                f"{requested_area_code} → {assigned_area_code}"
            )
            return True
        except Exception as e:
            logger.error(f"Failed to create area_code_fallback notification: {e}")
        return False

    async def notify_retry_attempt(
        self,
        user_id: str,
        verification_id: str,
        service: str,
        attempt: int,
        max_attempts: int,
        reason: str,
    ) -> bool:
        """Notify when retry attempt is made (v4.4.1 Phase 6)."""
        try:
            # Format reason for user-friendly display
            reason_map = {
                "area_code_mismatch": "area code didn't match",
                "carrier_mismatch": "carrier didn't match",
                "voip_detected": "VOIP number detected",
                "not_mobile": "landline number detected",
            }
            friendly_reason = reason_map.get(reason, reason.replace("_", " "))

            # Determine if this is the final attempt
            is_final = attempt == max_attempts

            if is_final:
                title = f"Final Retry Attempt ({attempt}/{max_attempts})"
                message = (
                    f"{service}: Accepting number on final attempt "
                    f"(reason: {friendly_reason})"
                )
            else:
                title = f"Retry {attempt}/{max_attempts}"
                message = f"{service}: Retrying purchase because {friendly_reason}"

            notification = self.notification_service.create_notification(
                user_id=user_id,
                notification_type="verification_retry",
                title=title,
                message=message,
            )
            self._broadcast_notification(user_id, notification)
            logger.info(
                f"Created verification_retry notification for {user_id}: "
                f"attempt {attempt}/{max_attempts}, reason={reason}"
            )
            return True
        except Exception as e:
            logger.error(f"Failed to create verification_retry notification: {e}")
        return False

    async def on_sms_received(self, verification) -> bool:
        """Notify when SMS is received for verification."""
        try:
            notification = self.notification_service.create_notification(
                user_id=verification.user_id,
                notification_type="sms_received",
                title="SMS Code Received",
                message=f"Verification code received for {verification.service_name}",
            )

            self._broadcast_notification(verification.user_id, notification)
            logger.info(f"Created sms_received notification for {verification.user_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to create sms_received notification: {e}")
        return False

    async def notify_low_balance(self, user_id: str, balance: float) -> bool:
        """Notify when user balance falls below threshold ($5.00)."""
        try:
            notification = self.notification_service.create_notification(
                user_id=user_id,
                notification_type="low_balance_warning",
                title="⚠️ Low Balance Alert",
                message=f"Your balance is low (${balance:.2f}). Please top up to avoid service interruption.",
            )
            self._broadcast_notification(user_id, notification)
            logger.info(f"Created low_balance_warning for {user_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to create low_balance notification: {e}")
        return False
