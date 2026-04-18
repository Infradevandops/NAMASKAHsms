"""Failed refund handling and retry service."""

from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional

from sqlalchemy.orm import Session

from app.core.logging import get_logger
from app.models.refund import Refund
from app.models.user import User
from app.services.notification_dispatcher import NotificationDispatcher

logger = get_logger(__name__)


class FailedRefundService:
    """Service for handling failed refunds with automatic retry logic."""

    MAX_RETRY_ATTEMPTS = 3
    RETRY_BACKOFF_MINUTES = [5, 15, 60]  # Exponential backoff: 5m, 15m, 60m

    def __init__(self, db: Session):
        self.db = db
        self.notifier = NotificationDispatcher(db)

    async def track_failed_refund(self, refund_id: str, error_message: str) -> Dict:
        """Track a failed refund and schedule retry.

        Args:
            refund_id: Refund identifier
            error_message: Error details

        Returns:
            Retry scheduling details
        """
        refund = self.db.query(Refund).filter(Refund.id == refund_id).first()
        if not refund:
            raise ValueError(f"Refund {refund_id} not found")

        # Parse existing failed attempts
        failed_attempts = (
            refund.failed_attempts.split(",") if refund.failed_attempts != "0" else []
        )
        attempt_count = len(failed_attempts)

        # Check if max attempts exceeded
        if attempt_count >= self.MAX_RETRY_ATTEMPTS:
            refund.status = "failed"
            refund.error_message = f"Max retry attempts ({self.MAX_RETRY_ATTEMPTS}) exceeded: {error_message}"
            refund.next_retry_at = None

            # Hold credit on user account
            user = self.db.query(User).filter(User.id == refund.user_id).first()
            if user:
                user.credit_hold_amount = float(refund.amount)
                user.credit_hold_reason = f"Failed refund {refund_id}: {error_message}"
                user.credit_hold_until = datetime.now(timezone.utc) + timedelta(days=30)

            logger.error(
                f"🚨 CRITICAL: Refund {refund_id} failed after {attempt_count} attempts. "
                f"Amount ${refund.amount} held on account. Error: {error_message}"
            )

            # Notify admin for manual intervention
            await self.notifier.send_notification(
                user_id=None,  # Admin notification
                notification_type="failed_refund_escalation",
                data={
                    "refund_id": refund_id,
                    "user_id": refund.user_id,
                    "amount": float(refund.amount),
                    "attempts": attempt_count,
                    "error": error_message,
                },
            )

            self.db.commit()

            return {
                "refund_id": refund_id,
                "status": "failed",
                "attempts": attempt_count,
                "escalated": True,
                "action": "Manual intervention required - credit held",
            }

        # Schedule retry
        backoff_minutes = self.RETRY_BACKOFF_MINUTES[
            min(attempt_count, len(self.RETRY_BACKOFF_MINUTES) - 1)
        ]
        next_retry_at = datetime.now(timezone.utc) + timedelta(minutes=backoff_minutes)

        failed_attempts.append(datetime.now(timezone.utc).isoformat())
        refund.failed_attempts = ",".join(failed_attempts)
        refund.next_retry_at = next_retry_at
        refund.status = "pending_retry"
        refund.error_message = error_message

        self.db.commit()

        logger.warning(
            f"Refund {refund_id} failed. Attempt {attempt_count + 1}/{self.MAX_RETRY_ATTEMPTS}. "
            f"Retrying in {backoff_minutes} minutes"
        )

        return {
            "refund_id": refund_id,
            "status": "pending_retry",
            "attempt": attempt_count + 1,
            "max_attempts": self.MAX_RETRY_ATTEMPTS,
            "next_retry_at": next_retry_at,
            "backoff_minutes": backoff_minutes,
        }

    async def get_failed_refunds_pending_retry(self) -> List[Dict]:
        """Get all failed refunds pending retry.

        Returns:
            List of refunds to retry
        """
        now = datetime.now(timezone.utc)

        refunds = (
            self.db.query(Refund)
            .filter(
                Refund.status == "pending_retry",
                Refund.next_retry_at <= now,
            )
            .all()
        )

        return [
            {
                "refund_id": r.id,
                "user_id": r.user_id,
                "amount": float(r.amount),
                "reason": r.reason,
                "attempts": len(r.failed_attempts.split(",")),
                "last_error": r.error_message,
                "next_retry_at": r.next_retry_at,
            }
            for r in refunds
        ]

    async def cancel_failed_refund(
        self, refund_id: str, notes: Optional[str] = None
    ) -> Dict:
        """Cancel a failed refund and manually credit user.

        Args:
            refund_id: Refund identifier
            notes: Cancellation notes

        Returns:
            Cancellation details
        """
        refund = self.db.query(Refund).filter(Refund.id == refund_id).first()
        if not refund:
            raise ValueError(f"Refund {refund_id} not found")

        # Manually credit the user
        user = self.db.query(User).filter(User.id == refund.user_id).first()
        if user:
            user.credits = float(user.credits) + float(refund.amount)
            user.credit_hold_amount = 0
            user.credit_hold_reason = None
            user.credit_hold_until = None

            logger.info(
                f"Failed refund {refund_id} manually processed. "
                f"User {refund.user_id} credited ${refund.amount}"
            )

        # Update refund status
        refund.status = "success"
        refund.processed_at = datetime.now(timezone.utc)
        self.db.commit()

        # Notify user
        await self.notifier.send_notification(
            user_id=refund.user_id,
            notification_type="refund_processed_manual",
            data={
                "refund_id": refund_id,
                "amount": float(refund.amount),
                "notes": notes or "Manual refund processing",
            },
        )

        return {
            "refund_id": refund_id,
            "status": "success",
            "amount_credited": float(refund.amount),
            "processed_at": refund.processed_at,
        }

    async def get_held_credits_by_user(self, user_id: str) -> Dict:
        """Get credit holds for a user.

        Args:
            user_id: User identifier

        Returns:
            Credit hold details
        """
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            raise ValueError(f"User {user_id} not found")

        if user.credit_hold_amount > 0:
            return {
                "user_id": user_id,
                "hold_amount": float(user.credit_hold_amount),
                "hold_reason": user.credit_hold_reason,
                "hold_until": user.credit_hold_until,
                "days_remaining": (
                    (user.credit_hold_until - datetime.now(timezone.utc)).days
                    if user.credit_hold_until
                    else 0
                ),
            }

        return {"user_id": user_id, "hold_amount": 0.0, "hold_reason": None}
