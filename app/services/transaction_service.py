"""Transaction logging service."""

import uuid
from datetime import datetime

from sqlalchemy.orm import Session

from app.models.transaction import Transaction


class TransactionService:
    """Log transactions for audit trail."""

    @staticmethod
    def log_sms_purchase(
        db: Session,
        user_id: str,
        cost: float,
        tier: str,
        service: str = None,
        filters: dict = None,
    ) -> str:
        """Log SMS purchase transaction."""
        if not filters:
            filters = {}

        transaction = Transaction(
            id=str(uuid.uuid4()),
            user_id=user_id,
            type="sms_purchase",
            amount=cost,
            tier=tier,
            service=service,
            filters=str(filters),
            status="completed",
            created_at=datetime.utcnow(),
        )
        db.add(transaction)
        db.commit()
        return transaction.id

    @staticmethod
    def log_api_key_creation(db: Session, user_id: str, key_id: str) -> str:
        """Log API key creation."""
        transaction = Transaction(
            id=str(uuid.uuid4()),
            user_id=user_id,
            type="api_key_created",
            amount=0.0,
            tier=None,
            service=key_id,
            status="completed",
            created_at=datetime.utcnow(),
        )
        db.add(transaction)
        db.commit()
        return transaction.id

    @staticmethod
    def log_filter_charge(db: Session, user_id: str, cost: float, filter_type: str, tier: str) -> str:
        """Log filter charge."""
        transaction = Transaction(
            id=str(uuid.uuid4()),
            user_id=user_id,
            type="filter_charge",
            amount=cost,
            tier=tier,
            service=filter_type,
            status="completed",
            created_at=datetime.utcnow(),
        )
        db.add(transaction)
        db.commit()
        return transaction.id

    @staticmethod
    def log_overage_charge(db: Session, user_id: str, cost: float, tier: str) -> str:
        """Log overage charge."""
        transaction = Transaction(
            id=str(uuid.uuid4()),
            user_id=user_id,
            type="overage_charge",
            amount=cost,
            tier=tier,
            status="completed",
            created_at=datetime.utcnow(),
        )
        db.add(transaction)
        db.commit()
        return transaction.id
