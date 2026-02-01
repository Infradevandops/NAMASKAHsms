"""
from datetime import datetime, timezone
from typing import Optional
from sqlalchemy.orm import Session
from app.core.logging import get_logger
from app.models.transaction import Transaction
from app.models.user import User
from app.models.verification import Verification
from app.services.credit_service import CreditService
from app.services.notification_dispatcher import NotificationDispatcher
from datetime import timedelta

AUTOMATIC REFUND SYSTEM - Critical Fix
=======================================
Implements automatic refunds for failed/timeout/cancelled verifications.
"""


logger = get_logger(__name__)


class AutoRefundService:

    """Automatic refund service for failed verifications."""

def __init__(self, db: Session):

        self.db = db
        self.credit_service = CreditService(db)

def process_verification_refund(self, verification_id: str, reason: str) -> Optional[dict]:

        """Process automatic refund for a failed verification.

        Args:
            verification_id: Verification ID
            reason: Refund reason (timeout, cancelled, failed)

        Returns:
            Refund details or None if already refunded
        """
        verification = self.db.query(Verification).filter(Verification.id == verification_id).first()

if not verification:
            logger.error(f"Verification {verification_id} not found")
            return None

        # Check if already refunded
        existing_refund = (
            self.db.query(Transaction)
            .filter(
                Transaction.user_id == verification.user_id,
                Transaction.type == "verification_refund",
                Transaction.description.contains(verification_id),
            )
            .first()
        )

if existing_refund:
            logger.info(f"Verification {verification_id} already refunded: {existing_refund.id}")
            return None

        # Only refund if status is timeout, cancelled, or failed
if verification.status not in ["timeout", "cancelled", "failed"]:
            logger.warning(f"Cannot refund verification {verification_id} with status: {verification.status}")
            return None

        # Get user
        user = self.db.query(User).filter(User.id == verification.user_id).first()
if not user:
            logger.error(f"User {verification.user_id} not found")
            return None

        # Calculate refund amount
        refund_amount = verification.cost

try:
            # Add credits back to user
            old_balance = user.credits
            user.credits = (user.credits or 0.0) + refund_amount

            # Create refund transaction
            transaction = Transaction(
                user_id=verification.user_id,
                amount=refund_amount,
                type="verification_refund",
                description=f"Auto-refund for {reason} verification {verification_id} ({verification.service_name})",
            )

            self.db.add(transaction)
            self.db.commit()

            new_balance = user.credits

            logger.info(
                f"✓ Auto-refund processed: Verification={verification_id}, "
                f"User={verification.user_id}, Amount=${refund_amount:.2f}, "
                f"Reason={reason}, Balance: ${old_balance:.2f} → ${new_balance:.2f}"
            )

            # CRITICAL: Send notification using dispatcher for real-time updates
try:

                notification_dispatcher = NotificationDispatcher(self.db)
                notification_dispatcher.on_refund_completed(
                    user_id=verification.user_id,
                    amount=refund_amount,
                    reference=f"auto-refund-{verification_id}",
                    new_balance=new_balance
                )
                self.db.commit()
                logger.info(f"✓ Refund notification sent to {verification.user_id}")
except Exception as e:
                logger.error(
                    f"🚨 CRITICAL: Refund notification failed for {verification.user_id}: {e}",
                    exc_info=True,
                )
                # Don't fail the refund, but ensure it's logged

            return {
                "verification_id": verification_id,
                "user_id": verification.user_id,
                "refund_amount": refund_amount,
                "reason": reason,
                "old_balance": old_balance,
                "new_balance": new_balance,
                "transaction_id": transaction.id,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }

except Exception as e:
            self.db.rollback()
            logger.error(
                f"Failed to process refund for verification {verification_id}: {str(e)}",
                exc_info=True,
            )
            return None

def reconcile_unrefunded_verifications(self, days_back: int = 30, dry_run: bool = True) -> dict:

        """Scan for unrefunded failed verifications and process refunds.

        Args:
            days_back: Number of days to look back
            dry_run: If True, only report without processing

        Returns:
            Reconciliation report
        """

        cutoff_date = datetime.now(timezone.utc) - timedelta(days=days_back)

        # Find failed verifications without refunds
        failed_verifications = (
            self.db.query(Verification)
            .filter(
                Verification.status.in_(["timeout", "cancelled", "failed"]),
                Verification.created_at >= cutoff_date,
            )
            .all()
        )

        report = {
            "total_failed": len(failed_verifications),
            "already_refunded": 0,
            "needs_refund": 0,
            "refunded_now": 0,
            "refund_errors": 0,
            "total_amount_refunded": 0.0,
            "verifications": [],
        }

for verification in failed_verifications:
            # Check if already refunded
            existing_refund = (
                self.db.query(Transaction)
                .filter(
                    Transaction.user_id == verification.user_id,
                    Transaction.type == "verification_refund",
                    Transaction.description.contains(verification.id),
                )
                .first()
            )

if existing_refund:
                report["already_refunded"] += 1
                continue

            report["needs_refund"] += 1

            verification_info = {
                "id": verification.id,
                "user_id": verification.user_id,
                "service": verification.service_name,
                "cost": verification.cost,
                "status": verification.status,
                "created_at": verification.created_at.isoformat(),
            }

if not dry_run:
                # Process refund
                result = self.process_verification_refund(verification.id, verification.status)
if result:
                    report["refunded_now"] += 1
                    report["total_amount_refunded"] += result["refund_amount"]
                    verification_info["refunded"] = True
                    verification_info["refund_amount"] = result["refund_amount"]
else:
                    report["refund_errors"] += 1
                    verification_info["refunded"] = False
                    verification_info["error"] = "Refund processing failed"
else:
                verification_info["refunded"] = False
                verification_info["dry_run"] = True

            report["verifications"].append(verification_info)

        logger.info(
            f"Reconciliation {'(DRY RUN)' if dry_run else ''}: "
            f"Total={report['total_failed']}, "
            f"Already Refunded={report['already_refunded']}, "
            f"Needs Refund={report['needs_refund']}, "
            f"Refunded Now={report['refunded_now']}, "
            f"Errors={report['refund_errors']}, "
            f"Amount=${report['total_amount_refunded']:.2f}"
        )

        return report