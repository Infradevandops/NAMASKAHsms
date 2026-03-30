"""Transaction recording service for analytics and audit."""

from datetime import datetime, timezone
from typing import Dict, Optional

from sqlalchemy.orm import Session

from app.core.logging import get_logger
from app.models.transaction import Transaction

logger = get_logger(__name__)


class TransactionService:
    """Record all financial transactions for analytics."""

    @staticmethod
    def record_sms_purchase(
        db: Session,
        user_id: str,
        amount: float,
        service: str,
        verification_id: str,
        old_balance: float,
        new_balance: float,
        filters: Optional[Dict] = None,
        tier: Optional[str] = None,
    ) -> Transaction:
        """Record SMS purchase transaction.

        This creates an audit trail for:
        - Analytics dashboards
        - Spending reports
        - User transaction history
        - Admin monitoring
        """
        transaction = Transaction(
            user_id=user_id,
            amount=-abs(amount),  # Negative for debit
            type="sms_purchase",
            description=f"SMS verification for {service}",
            tier=tier,
            service=service,
            filters=str(filters) if filters else None,
            status="completed",
            reference=f"sms_{verification_id}",
        )

        db.add(transaction)
        db.flush()

        logger.info(
            f"Transaction recorded: user={user_id}, amount=${amount:.2f}, "
            f"balance: ${old_balance:.2f} → ${new_balance:.2f}"
        )

        return transaction

    @staticmethod
    def record_credit_addition(
        db: Session,
        user_id: str,
        amount: float,
        payment_reference: str,
        payment_method: str = "paystack",
    ) -> Transaction:
        """Record credit addition (top-up)."""
        transaction = Transaction(
            user_id=user_id,
            amount=abs(amount),  # Positive for credit
            type="credit",
            description=f"Credit added via {payment_method}",
            status="completed",
            reference=payment_reference,
        )

        db.add(transaction)
        db.flush()

        logger.info(f"Credit added: user={user_id}, amount=${amount:.2f}")
        return transaction

    @staticmethod
    def record_refund(
        db: Session,
        user_id: str,
        amount: float,
        verification_id: str,
        reason: str,
    ) -> Transaction:
        """Record refund transaction."""
        transaction = Transaction(
            user_id=user_id,
            amount=abs(amount),  # Positive for refund
            type="refund",
            description=f"Refund: {reason}",
            status="completed",
            reference=f"refund_{verification_id}",
        )

        db.add(transaction)
        db.flush()

        logger.info(f"Refund recorded: user={user_id}, amount=${amount:.2f}")
        return transaction
