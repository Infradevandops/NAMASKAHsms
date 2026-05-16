"""
Automatic refund service for failed verifications.
CRITICAL FIX: Implements automatic refunds for failed/timeout/cancelled verifications.
"""

from datetime import datetime, timedelta, timezone
from typing import Optional

from sqlalchemy.orm import Session

from app.core.logging import get_logger
from app.models.transaction import Transaction
from app.models.user import User
from app.models.verification import Verification
from app.services.credit_service import CreditService
from app.services.notification_dispatcher import NotificationDispatcher

logger = get_logger(__name__)


class AutoRefundService:
    """Automatic refund service for failed verifications."""

    def __init__(self, db: Session):
        self.db = db
        self.credit_service = CreditService(db)

    async def process_verification_refund(
        self, verification_id: str, reason: str
    ) -> Optional[dict]:
        """Process automatic refund for a failed verification."""
        verification = (
            self.db.query(Verification)
            .filter(Verification.id == verification_id)
            .first()
        )

        if not verification:
            logger.error(f"Verification {verification_id} not found")
            return None

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
            logger.info(
                f"Verification {verification_id} already refunded: {existing_refund.id}"
            )
            return None

        # PRODUCTION FIX: Allow "error" status for refunds (common failure state)
        refundable_statuses = ["timeout", "cancelled", "failed", "error"]
        if verification.status not in refundable_statuses:
            logger.warning(
                f"Cannot refund verification {verification_id} with status: {verification.status}. "
                f"Refundable statuses: {refundable_statuses}"
            )
            return None

        user = self.db.query(User).filter(User.id == verification.user_id).first()
        if not user:
            logger.error(f"User {verification.user_id} not found")
            return None

        refund_amount = verification.cost

        try:
            # PRODUCTION FIX: Handle Decimal/float type mismatch from database
            old_balance = float(user.credits) if user.credits else 0.0
            refund_amount_float = float(refund_amount)
            user.credits = old_balance + refund_amount_float

            # Mark verification as refunded with proper type handling
            verification.refunded = True
            verification.refund_amount = refund_amount_float
            verification.refund_reason = reason
            verification.refunded_at = datetime.now(timezone.utc)

            logger.debug(
                f"Refund staged: verification={verification_id}, "
                f"amount=${refund_amount_float:.2f}, "
                f"old_balance=${old_balance:.2f}, "
                f"new_balance=${user.credits:.2f}"
            )

            # Sync to PurchaseOutcome telemetry
            from sqlalchemy import update

            from app.models.purchase_outcome import PurchaseOutcome

            try:
                stmt_po = (
                    update(PurchaseOutcome)
                    .where(PurchaseOutcome.verification_id == str(verification.id))
                    .values(
                        is_refunded=True,
                        refund_amount=float(refund_amount),
                        refund_reason=reason,
                    )
                )
                self.db.execute(stmt_po)
            except Exception as e:
                logger.error(f"Failed to sync refund to PurchaseOutcome: {e}")

            # Phase 11 & 12: Institutional Transparency & Financial Integrity
            display_reason = reason.replace("_", " ").title()
            if reason == "sms_timeout":
                display_reason = "Carrier Delivery Failure"
            elif reason == "area_code_mismatch":
                display_reason = "Area Code Mismatch"

            import uuid

            from app.core.constants import TransactionType
            from app.models.balance_transaction import BalanceTransaction

            # 1. Create BalanceTransaction (for accounting) with proper type handling
            balance_tx = BalanceTransaction(
                id=str(uuid.uuid4()),
                user_id=verification.user_id,
                amount=abs(refund_amount_float),
                type=TransactionType.REFUND,
                description=f"Refund: {verification.service_name} ({display_reason})",
                balance_after=float(user.credits),
                created_at=datetime.now(timezone.utc),
            )
            self.db.add(balance_tx)
            self.db.flush()

            logger.debug(f"BalanceTransaction created: {balance_tx.id}")

            # 2. Create Transaction (for analytics/history) with idempotency
            transaction_reference = f"refund_{verification.id}"

            # Check for duplicate transaction (idempotency)
            existing_tx = (
                self.db.query(Transaction)
                .filter(Transaction.reference == transaction_reference)
                .first()
            )

            if existing_tx:
                logger.warning(
                    f"Transaction already exists for verification {verification_id}: {existing_tx.id}. "
                    f"Using existing transaction."
                )
                transaction = existing_tx
            else:
                transaction = Transaction(
                    id=str(uuid.uuid4()),
                    user_id=verification.user_id,
                    amount=refund_amount_float,
                    type="verification_refund",
                    description=f"Auto-refund: {verification.service_name} ({display_reason})",
                    status="completed",
                    reference=transaction_reference,
                    created_at=datetime.now(timezone.utc),
                )
                self.db.add(transaction)
                logger.debug(f"Transaction created: {transaction.id}")

            # Link verification to balance transaction
            verification.refund_transaction_id = balance_tx.id

            # ATOMIC COMMIT: Only commit once all ledger and tracking records are staged
            self.db.commit()

            # --- INSTITUTIONAL TELEMETRY ---
            # Sync refund details to PurchaseOutcome
            from app.services.purchase_intelligence import PurchaseIntelligenceService

            # Use current time as processed_at
            processed_at = datetime.now(timezone.utc)

            # If verification.refunded_at was set earlier in this method (line 79)
            # we can use it as a reference for requested_at if needed,
            # but usually requested_at is when the decision to refund was made.

            import asyncio

            asyncio.create_task(
                PurchaseIntelligenceService.update_sms_received(
                    verification_id=str(verification.id),
                    sms_received=False,  # Still False since it's a refund
                    refund_reason=reason,
                    refund_transaction_id=balance_tx.id,
                    refund_requested_at=verification.refunded_at,  # already set at line 79
                    refund_processed_at=processed_at,
                )
            )

            new_balance = user.credits

            logger.info(
                f"✓ Auto-refund processed: Verification={verification_id}, "
                f"User={verification.user_id}, Amount=${refund_amount:.2f}, "
                f"Reason={reason}, Balance: ${old_balance:.2f} → ${new_balance:.2f}"
            )

            try:
                notification_dispatcher = NotificationDispatcher(self.db)
                if reason == "timeout":
                    await notification_dispatcher.notify_verification_timeout(
                        user_id=verification.user_id,
                        verification_id=verification_id,
                        service=verification.service_name,
                        refund_amount=refund_amount,
                    )
                elif reason == "cancelled":
                    await notification_dispatcher.notify_verification_cancelled(
                        user_id=verification.user_id,
                        verification_id=verification_id,
                        service=verification.service_name,
                        refund_amount=refund_amount,
                        new_balance=new_balance,
                    )
                else:
                    await notification_dispatcher.notify_verification_failed(
                        user_id=verification.user_id,
                        verification_id=verification_id,
                        service=verification.service_name,
                        reason=f"Refunded: {reason}",
                    )

                logger.info(f"✓ Refund notification sent to {verification.user_id}")
            except Exception as e:
                logger.error(
                    f"🚨 CRITICAL: Refund notification failed for {verification.user_id}: {e}",
                    exc_info=True,
                )

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

            # Enhanced error logging for production debugging
            error_context = {
                "verification_id": verification_id,
                "user_id": verification.user_id if verification else None,
                "refund_amount": (
                    refund_amount_float if "refund_amount_float" in locals() else None
                ),
                "old_balance": old_balance if "old_balance" in locals() else None,
                "reason": reason,
                "error_type": type(e).__name__,
                "error_message": str(e),
            }

            logger.error(
                f"🚨 REFUND FAILED: {error_context}",
                exc_info=True,
            )

            # Return error details for monitoring
            return {
                "error": True,
                "verification_id": verification_id,
                "error_type": type(e).__name__,
                "error_message": str(e),
                "context": error_context,
            }

    def reconcile_unrefunded_verifications(
        self, days_back: int = 30, dry_run: bool = True
    ) -> dict:
        """Scan for unrefunded failed verifications and process refunds."""
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=days_back)

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
                import asyncio

                result = asyncio.run(
                    self.process_verification_refund(
                        verification.id, verification.status
                    )
                )
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
