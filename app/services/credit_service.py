"""Credit system service for managing user credits and transactions."""


from datetime import datetime, timezone
from typing import Any, Dict, Optional
from sqlalchemy import desc
from sqlalchemy.orm import Session
from app.core.exceptions import InsufficientCreditsError
from app.core.logging import get_logger
from app.models.transaction import Transaction
from app.models.user import User
from app.services.notification_dispatcher import NotificationDispatcher

logger = get_logger(__name__)


class CreditService:

    """Service for managing user credits and transactions."""

    def __init__(self, db: Session):

        """Initialize credit service with database session."""
        self.db = db
        self.notification_dispatcher = NotificationDispatcher(db)

    def get_balance(self, user_id: str) -> float:

        """Get current credit balance for user.

        Args:
            user_id: User ID

        Returns:
            Current credit balance as float

        Raises:
            ValueError: If user not found
        """
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            raise ValueError(f"User {user_id} not found")

        logger.info(f"Retrieved balance for user {user_id}: {user.credits}")
        return float(user.credits or 0.0)

    def add_credits(

        self,
        user_id: str,
        amount: float,
        description: str = "Manual credit addition",
        transaction_type: str = "credit",
        ) -> Dict[str, Any]:
        """Add credits to user account.

        Args:
            user_id: User ID
            amount: Amount to add (must be positive)
            description: Transaction description
            transaction_type: Type of transaction (credit, bonus, refund)

        Returns:
            Dictionary with transaction details

        Raises:
            ValueError: If amount invalid or user not found
        """
        # Validate amount
        if amount <= 0:
            raise ValueError("Amount must be positive")

        # Get user
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            raise ValueError(f"User {user_id} not found")

        # Add credits
        old_balance = float(user.credits or 0.0)
        user.credits = (user.credits or 0.0) + amount

        # Create transaction record
        transaction = Transaction(
            user_id=user_id,
            amount=amount,
            type=transaction_type,
            description=description,
        )

        self.db.add(transaction)
        self.db.commit()

        new_balance = float(user.credits)

        # CRITICAL: Notify user of credit addition
        self.notification_dispatcher.on_credits_added(
            user_id=user_id,
            amount=amount,
            reason=description,
            new_balance=new_balance
        )

        logger.info(
            f"Added {amount} credits to user {user_id}. "
            f"Balance: {old_balance} -> {new_balance}. "
            f"Type: {transaction_type}. Description: {description}"
        )

        return {
            "user_id": user_id,
            "amount_added": amount,
            "old_balance": old_balance,
            "new_balance": new_balance,
            "transaction_type": transaction_type,
            "description": description,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    def deduct_credits(

        self,
        user_id: str,
        amount: float,
        description: str = "Service charge",
        transaction_type: str = "debit",
        ) -> Dict[str, Any]:
        """Deduct credits from user account.

        Args:
            user_id: User ID
            amount: Amount to deduct (must be positive)
            description: Transaction description
            transaction_type: Type of transaction (debit, refund)

        Returns:
            Dictionary with transaction details

        Raises:
            ValueError: If amount invalid or user not found
            InsufficientCreditsError: If user has insufficient credits
        """
        # Validate amount
        if amount <= 0:
            raise ValueError("Amount must be positive")

        # Get user
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            raise ValueError(f"User {user_id} not found")

        # Check sufficient credits
        current_balance = float(user.credits or 0.0)
        if current_balance < amount:
            logger.warning(
                f"Insufficient credits for user {user_id}. " f"Required: {amount}, Available: {current_balance}"
            )
            raise InsufficientCreditsError(f"Insufficient credits. Required: {amount}, Available: {current_balance}")

        # Deduct credits
        old_balance = current_balance
        user.credits = current_balance - amount

        # Create transaction record
        transaction = Transaction(
            user_id=user_id,
            amount=-amount,  # Negative for debit
            type=transaction_type,
            description=description,
        )

        self.db.add(transaction)
        self.db.commit()

        new_balance = float(user.credits)

        # CRITICAL: Notify user of credit deduction
        self.notification_dispatcher.on_credits_deducted_enhanced(
            user_id=user_id,
            amount=amount,
            reason=description,
            new_balance=new_balance
        )

        logger.info(
            f"Deducted {amount} credits from user {user_id}. "
            f"Balance: {old_balance} -> {new_balance}. "
            f"Type: {transaction_type}. Description: {description}"
        )

        return {
            "user_id": user_id,
            "amount_deducted": amount,
            "old_balance": old_balance,
            "new_balance": new_balance,
            "transaction_type": transaction_type,
            "description": description,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    def get_transaction_history(

        self,
        user_id: str,
        transaction_type: Optional[str] = None,
        skip: int = 0,
        limit: int = 20,
        ) -> Dict[str, Any]:
        """Get transaction history for user.

        Args:
            user_id: User ID
            transaction_type: Filter by type (credit, debit, bonus, refund)
            skip: Number of records to skip
            limit: Number of records to return (max 100)

        Returns:
            Dictionary with transaction history and metadata
        """
        # Validate user exists
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            raise ValueError(f"User {user_id} not found")

        # Build query
        query = self.db.query(Transaction).filter(Transaction.user_id == user_id)

        # Apply type filter
        if transaction_type:
            query = query.filter(Transaction.type == transaction_type)

        # Get total count
        total = query.count()

        # Apply pagination and sorting
        transactions = query.order_by(desc(Transaction.created_at)).offset(skip).limit(min(limit, 100)).all()

        logger.info(
            f"Retrieved {len(transactions)} transactions for user {user_id} "
            f"(total: {total}, skip: {skip}, limit: {limit})"
        )

        return {
            "user_id": user_id,
            "total": total,
            "skip": skip,
            "limit": limit,
            "transactions": [
                {
                    "id": t.id,
                    "amount": float(t.amount),
                    "type": t.type,
                    "description": t.description,
                    "created_at": t.created_at.isoformat() if t.created_at else None,
                }
        for t in transactions
            ],
        }

    def get_transaction_summary(self, user_id: str) -> Dict[str, Any]:

        """Get summary of transactions for user.

        Args:
            user_id: User ID

        Returns:
            Dictionary with transaction summary
        """
        # Validate user exists
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            raise ValueError(f"User {user_id} not found")

        # Get all transactions
        transactions = self.db.query(Transaction).filter(Transaction.user_id == user_id).all()

        # Calculate totals by type
        summary = {
            "user_id": user_id,
            "current_balance": float(user.credits or 0.0),
            "total_credits_added": 0.0,
            "total_credits_deducted": 0.0,
            "total_bonuses": 0.0,
            "total_refunds": 0.0,
            "transaction_count": len(transactions),
        }

        for t in transactions:
            amount = float(t.amount)
        if t.type == "credit":
                summary["total_credits_added"] += max(0, amount)
        elif t.type == "debit":
                summary["total_credits_deducted"] += abs(min(0, amount))
        elif t.type == "bonus":
                summary["total_bonuses"] += max(0, amount)
        elif t.type == "refund":
                summary["total_refunds"] += max(0, amount)

        logger.info(f"Generated transaction summary for user {user_id}")

        return summary

    def transfer_credits(

        self,
        from_user_id: str,
        to_user_id: str,
        amount: float,
        description: str = "Credit transfer",
        ) -> Dict[str, Any]:
        """Transfer credits from one user to another.

        Args:
            from_user_id: Source user ID
            to_user_id: Destination user ID
            amount: Amount to transfer
            description: Transfer description

        Returns:
            Dictionary with transfer details

        Raises:
            ValueError: If users not found or amount invalid
            InsufficientCreditsError: If source user has insufficient credits
        """
        # Validate amount
        if amount <= 0:
            raise ValueError("Amount must be positive")

        # Get users
        from_user = self.db.query(User).filter(User.id == from_user_id).first()
        to_user = self.db.query(User).filter(User.id == to_user_id).first()

        if not from_user:
            raise ValueError(f"Source user {from_user_id} not found")
        if not to_user:
            raise ValueError(f"Destination user {to_user_id} not found")

        # Check sufficient credits
        if (from_user.credits or 0.0) < amount:
            raise InsufficientCreditsError(
                "Insufficient credits for transfer. " f"Required: {amount}, Available: {from_user.credits}"
            )

        # Perform transfer
        from_user.credits = (from_user.credits or 0.0) - amount
        to_user.credits = (to_user.credits or 0.0) + amount

        # Create transaction records
        from_transaction = Transaction(
            user_id=from_user_id,
            amount=-amount,
            type="transfer",
            description=f"Transfer to {to_user_id}: {description}",
        )

        to_transaction = Transaction(
            user_id=to_user_id,
            amount=amount,
            type="transfer",
            description=f"Transfer from {from_user_id}: {description}",
        )

        self.db.add(from_transaction)
        self.db.add(to_transaction)
        self.db.commit()

        logger.info(f"Transferred {amount} credits from {from_user_id} to {to_user_id}. " f"Description: {description}")

        return {
            "from_user_id": from_user_id,
            "to_user_id": to_user_id,
            "amount": amount,
            "from_user_new_balance": float(from_user.credits),
            "to_user_new_balance": float(to_user.credits),
            "description": description,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    def reset_credits(self, user_id: str, new_amount: float = 0.0) -> Dict[str, Any]:

        """Reset user credits (admin only).

        Args:
            user_id: User ID
            new_amount: New credit amount

        Returns:
            Dictionary with reset details

        Raises:
            ValueError: If user not found or amount invalid
        """
        # Validate amount
        if new_amount < 0:
            raise ValueError("Amount cannot be negative")

        # Get user
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            raise ValueError(f"User {user_id} not found")

        old_balance = float(user.credits or 0.0)
        user.credits = new_amount

        # Create transaction record
        transaction = Transaction(
            user_id=user_id,
            amount=new_amount - old_balance,
            type="admin_reset",
            description=f"Admin reset from {old_balance} to {new_amount}",
        )

        self.db.add(transaction)
        self.db.commit()

        logger.warning(f"Admin reset credits for user {user_id}. " f"Balance: {old_balance} -> {new_amount}")

        return {
            "user_id": user_id,
            "old_balance": old_balance,
            "new_balance": new_amount,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
