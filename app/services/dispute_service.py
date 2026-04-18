"""Dispute service for handling payment disputes and chargebacks."""

from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional

from sqlalchemy.orm import Session

from app.core.logging import get_logger
from app.models.dispute import Dispute
from app.models.transaction import PaymentLog
from app.models.user import User
from app.services.notification_dispatcher import NotificationDispatcher

logger = get_logger(__name__)


class DisputeService:
    """Service for managing payment disputes and chargebacks."""

    def __init__(self, db: Session):
        self.db = db
        self.notifier = NotificationDispatcher(db)

    async def open_dispute(
        self,
        user_id: str,
        payment_id: str,
        reason_code: str,
        reason_description: str,
        amount: float,
    ) -> Dict:
        """Open a new payment dispute.

        Args:
            user_id: User initiating dispute
            payment_id: Payment log ID
            reason_code: Chargeback reason code
            reason_description: Detailed reason
            amount: Dispute amount

        Returns:
            Created dispute details
        """
        # Validate reason code
        if reason_code not in Dispute.CHARGEBACK_REASONS:
            raise ValueError(f"Invalid reason code: {reason_code}")

        # Validate payment exists
        payment = (
            self.db.query(PaymentLog)
            .filter(PaymentLog.id == payment_id, PaymentLog.user_id == user_id)
            .first()
        )
        if not payment:
            raise ValueError(f"Payment {payment_id} not found for user {user_id}")

        # Create dispute
        dispute = Dispute(
            user_id=user_id,
            payment_log_id=payment_id,
            amount=amount,
            reason_code=reason_code,
            reason_description=reason_description,
            dispute_date=datetime.now(timezone.utc),
            status="opened",
        )

        self.db.add(dispute)
        self.db.commit()

        logger.info(
            f"Dispute opened for user {user_id}: "
            f"Payment {payment_id}, Amount ${amount}, Reason: {reason_code}"
        )

        # Notify admin
        await self.notifier.send_notification(
            user_id=None,  # Admin notification
            notification_type="dispute_opened",
            data={
                "dispute_id": dispute.id,
                "user_id": user_id,
                "amount": amount,
                "reason": reason_code,
            },
        )

        return {
            "dispute_id": dispute.id,
            "user_id": user_id,
            "payment_id": payment_id,
            "amount": amount,
            "reason_code": reason_code,
            "status": dispute.status,
            "created_at": dispute.created_at,
        }

    async def process_chargeback(
        self, dispute_id: str, resolution: str, notes: str
    ) -> Dict:
        """Process a dispute (won/lost/appealed).

        Args:
            dispute_id: Dispute identifier
            resolution: Resolution (won, lost, appealed)
            notes: Resolution notes

        Returns:
            Updated dispute details
        """
        dispute = self.db.query(Dispute).filter(Dispute.id == dispute_id).first()
        if not dispute:
            raise ValueError(f"Dispute {dispute_id} not found")

        if resolution not in ["won", "lost", "appealed"]:
            raise ValueError(f"Invalid resolution: {resolution}")

        dispute.resolution = resolution
        dispute.resolution_date = datetime.now(timezone.utc)
        dispute.resolution_notes = notes
        dispute.status = (
            "won"
            if resolution == "won"
            else ("lost" if resolution == "lost" else "appealed")
        )

        # Handle balance reversal for lost disputes
        if resolution == "lost":
            user = self.db.query(User).filter(User.id == dispute.user_id).first()
            if user:
                # Hold credit to prevent further spending
                user.credit_hold_amount = dispute.amount
                user.credit_hold_reason = f"Chargeback lost: {dispute.reason_code}"
                user.credit_hold_until = datetime.now(timezone.utc) + timedelta(days=30)

                dispute.balance_reversed = True
                dispute.reversal_amount = dispute.amount
                dispute.reversal_at = datetime.now(timezone.utc)

                logger.warning(
                    f"Chargeback lost for user {dispute.user_id}: "
                    f"${dispute.amount} held, expires {user.credit_hold_until}"
                )

        self.db.commit()

        # Notify user
        await self.notifier.send_notification(
            user_id=dispute.user_id,
            notification_type="dispute_resolved",
            data={
                "dispute_id": dispute.id,
                "resolution": resolution,
                "amount": dispute.amount,
            },
        )

        return {
            "dispute_id": dispute.id,
            "status": dispute.status,
            "resolution": resolution,
            "resolved_at": dispute.resolution_date,
            "balance_reversed": dispute.balance_reversed,
        }

    async def get_open_disputes(
        self, user_id: Optional[str] = None
    ) -> List[Dict]:
        """Get open disputes for user or all open disputes.

        Args:
            user_id: Filter to specific user (None = all)

        Returns:
            List of open disputes
        """
        query = self.db.query(Dispute).filter(Dispute.status == "opened")

        if user_id:
            query = query.filter(Dispute.user_id == user_id)

        disputes = query.all()

        return [
            {
                "dispute_id": d.id,
                "user_id": d.user_id,
                "amount": d.amount,
                "reason_code": d.reason_code,
                "status": d.status,
                "opened_at": d.created_at,
                "days_open": (datetime.now(timezone.utc) - d.created_at).days,
            }
            for d in disputes
        ]

    async def appeal_dispute(self, dispute_id: str, appeal_notes: str) -> Dict:
        """Appeal a lost dispute.

        Args:
            dispute_id: Dispute identifier
            appeal_notes: Appeal justification

        Returns:
            Updated dispute details
        """
        dispute = self.db.query(Dispute).filter(Dispute.id == dispute_id).first()
        if not dispute:
            raise ValueError(f"Dispute {dispute_id} not found")

        if dispute.resolution != "lost":
            raise ValueError(
                "Can only appeal lost disputes. Current resolution: "
                + str(dispute.resolution)
            )

        dispute.status = "appealed"
        dispute.resolution = "appealed"
        dispute.resolution_notes = appeal_notes
        self.db.commit()

        logger.info(f"Dispute {dispute_id} appealed: {appeal_notes}")

        return {
            "dispute_id": dispute.id,
            "status": dispute.status,
            "resolution": dispute.resolution,
        }
