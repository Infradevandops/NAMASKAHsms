"""Reconciliation service for balance verification and reconciliation."""

from datetime import datetime, timezone
from typing import Dict, Optional

from sqlalchemy.orm import Session

from app.core.logging import get_logger
from app.models.balance_transaction import BalanceTransaction
from app.models.reconciliation_log import BalanceMismatchAlert, ReconciliationLog
from app.models.user import User

logger = get_logger(__name__)


class ReconciliationService:
    """Service for reconciling user balances and detecting mismatches."""

    def __init__(self, db: Session):
        self.db = db

    async def reconcile_user_wallet(
        self, user_id: str, period_start: datetime, period_end: datetime
    ) -> Dict:
        """Reconcile user wallet for a specific period.

        Args:
            user_id: User identifier
            period_start: Period start date
            period_end: Period end date

        Returns:
            Reconciliation result with status and discrepancies
        """
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            raise ValueError(f"User {user_id} not found")

        # Get current balance
        current_balance = float(user.credits)

        # Calculate expected balance from transactions
        transactions = (
            self.db.query(BalanceTransaction)
            .filter(
                BalanceTransaction.user_id == user_id,
                BalanceTransaction.created_at >= period_start,
                BalanceTransaction.created_at <= period_end,
            )
            .all()
        )

        total_debits = sum(t.amount for t in transactions if t.type == "debit")
        total_credits = sum(t.amount for t in transactions if t.type == "credit")
        transaction_count = len(transactions)

        expected_balance = total_credits - total_debits

        # Calculate discrepancy
        discrepancy = current_balance - expected_balance
        discrepancy_percentage = (
            (abs(discrepancy) / expected_balance * 100) if expected_balance != 0 else 0
        )

        # Create reconciliation log
        reconciliation = ReconciliationLog(
            user_id=user_id,
            account_type="user_wallet",
            reconciliation_period=period_start,
            reconciliation_end=period_end,
            expected_balance=expected_balance,
            actual_balance=current_balance,
            discrepancy_amount=discrepancy,
            total_debits=total_debits,
            total_credits=total_credits,
            transaction_count=transaction_count,
            status="pending" if discrepancy != 0 else "reconciled",
            is_critical=abs(discrepancy_percentage) > 5.0,  # > 5% is critical
            started_at=datetime.now(timezone.utc),
        )

        self.db.add(reconciliation)

        # Create alert if discrepancy exists
        if discrepancy != 0:
            alert = BalanceMismatchAlert(
                user_id=user_id,
                mismatch_amount=abs(discrepancy),
                percentage_diff=discrepancy_percentage,
                expected_balance=expected_balance,
                actual_balance=current_balance,
                severity=(
                    "critical"
                    if discrepancy_percentage > 5.0
                    else ("high" if discrepancy_percentage > 2.0 else "medium")
                ),
                requires_manual_review=discrepancy_percentage > 2.0,
            )
            self.db.add(alert)
            logger.warning(
                f"Balance mismatch for user {user_id}: "
                f"Expected {expected_balance}, Got {current_balance}, "
                f"Diff: {discrepancy} ({discrepancy_percentage:.2f}%)"
            )

        self.db.commit()

        return {
            "reconciliation_id": reconciliation.id,
            "user_id": user_id,
            "current_balance": current_balance,
            "expected_balance": expected_balance,
            "discrepancy": discrepancy,
            "discrepancy_percentage": discrepancy_percentage,
            "status": reconciliation.status,
            "is_critical": reconciliation.is_critical,
            "transactions_checked": transaction_count,
        }

    async def check_and_alert_mismatch(self, user_id: str) -> Optional[Dict]:
        """Check for balance mismatch and create alert if found.

        Args:
            user_id: User identifier

        Returns:
            Alert details if mismatch found, None otherwise
        """
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            return None

        current_balance = float(user.credits)

        # Get total from all transactions
        transactions = (
            self.db.query(BalanceTransaction)
            .filter(BalanceTransaction.user_id == user_id)
            .all()
        )

        total_debits = sum(t.amount for t in transactions if t.type == "debit")
        total_credits = sum(t.amount for t in transactions if t.type == "credit")
        expected_balance = total_credits - total_debits

        discrepancy = current_balance - expected_balance
        discrepancy_percentage = (
            (abs(discrepancy) / expected_balance * 100) if expected_balance != 0 else 0
        )

        if discrepancy != 0:
            alert = BalanceMismatchAlert(
                user_id=user_id,
                mismatch_amount=abs(discrepancy),
                percentage_diff=discrepancy_percentage,
                expected_balance=expected_balance,
                actual_balance=current_balance,
                severity=(
                    "critical"
                    if discrepancy_percentage > 5.0
                    else ("high" if discrepancy_percentage > 2.0 else "medium")
                ),
            )
            self.db.add(alert)
            self.db.commit()

            logger.error(
                f"🚨 MISMATCH ALERT: User {user_id} - "
                f"Balance mismatch detected: {discrepancy} "
                f"({discrepancy_percentage:.2f}%)"
            )

            return {
                "alert_id": alert.id,
                "user_id": user_id,
                "expected": expected_balance,
                "actual": current_balance,
                "discrepancy": discrepancy,
                "percentage": discrepancy_percentage,
                "severity": alert.severity,
            }

        return None

    async def resolve_mismatch(
        self, alert_id: str, resolution: str, notes: Optional[str] = None
    ) -> Dict:
        """Resolve a balance mismatch alert.

        Args:
            alert_id: Alert identifier
            resolution: Resolution type (auto_resolved, manual_resolved, not_resolved)
            notes: Resolution notes

        Returns:
            Updated alert details
        """
        alert = (
            self.db.query(BalanceMismatchAlert)
            .filter(BalanceMismatchAlert.id == alert_id)
            .first()
        )
        if not alert:
            raise ValueError(f"Alert {alert_id} not found")

        alert.status = "resolved" if "resolved" in resolution else "dismissed"
        alert.resolution_notes = notes
        alert.resolved_at = datetime.now(timezone.utc)
        self.db.commit()

        logger.info(
            f"Balance mismatch alert {alert_id} resolved: {resolution} - {notes}"
        )

        return {
            "alert_id": alert.id,
            "status": alert.status,
            "resolved_at": alert.resolved_at,
        }
