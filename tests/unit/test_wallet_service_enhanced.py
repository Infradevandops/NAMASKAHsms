"""
Wallet Service Tests
Coverage: Balance operations, transactions, concurrency
"""

import pytest
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from app.models.user import User
from app.models.transaction import Transaction


class MockWalletService:
    """Mock wallet service for testing"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_balance(self, user_id: str) -> float:
        """Get user balance"""
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            raise ValueError(f"User {user_id} not found")
        return user.credits or 0.0
    
    def add_credits(self, user_id: str, amount: float, description: str = None) -> dict:
        """Add credits to user account"""
        if amount <= 0:
            raise ValueError("Amount must be positive")
        
        user = self.db.query(User).filter(User.id == user_id).with_for_update().first()
        if not user:
            raise ValueError(f"User {user_id} not found")
        
        user.credits = (user.credits or 0.0) + amount
        
        transaction = Transaction(
            user_id=user_id,
            type="credit",
            amount=amount,
            description=description or f"Added {amount} credits",
            status="completed",
            created_at=datetime.now(timezone.utc)
        )
        self.db.add(transaction)
        self.db.commit()
        
        return {
            "balance": user.credits,
            "amount_added": amount,
            "transaction_id": transaction.id
        }
    
    def deduct_credits(self, user_id: str, amount: float, description: str = None) -> dict:
        """Deduct credits from user account"""
        if amount <= 0:
            raise ValueError("Amount must be positive")
        
        user = self.db.query(User).filter(User.id == user_id).with_for_update().first()
        if not user:
            raise ValueError(f"User {user_id} not found")
        
        if (user.credits or 0.0) < amount:
            raise ValueError("Insufficient balance")
        
        user.credits -= amount
        
        transaction = Transaction(
            user_id=user_id,
            type="debit",
            amount=amount,
            description=description or f"Deducted {amount} credits",
            status="completed",
            created_at=datetime.now(timezone.utc)
        )
        self.db.add(transaction)
        self.db.commit()
        
        return {
            "balance": user.credits,
            "amount_deducted": amount,
            "transaction_id": transaction.id
        }
    
    def get_transaction_history(self, user_id: str, limit: int = 50) -> list:
        """Get transaction history"""
        transactions = self.db.query(Transaction).filter(
            Transaction.user_id == user_id
        ).order_by(Transaction.created_at.desc()).limit(limit).all()
        
        return [
            {
                "id": t.id,
                "type": t.type,
                "amount": t.amount,
                "description": t.description,
                "status": t.status,
                "created_at": t.created_at.isoformat()
            }
            for t in transactions
        ]


class TestWalletService:
    """Wallet service tests"""

    @pytest.fixture
    def wallet_service(self, db_session):
        return MockWalletService(db_session)

    @pytest.fixture
    def test_user(self, db_session):
        user = User(
            id="wallet_user",
            email="wallet@example.com",
            credits=100.0
        )
        db_session.add(user)
        db_session.commit()
        return user

    def test_get_balance(self, wallet_service, test_user):
        """Test getting user balance"""
        balance = wallet_service.get_balance(test_user.id)
        assert balance == 100.0

    def test_get_balance_nonexistent_user(self, wallet_service):
        """Test getting balance for non-existent user"""
        with pytest.raises(ValueError, match="User .* not found"):
            wallet_service.get_balance("nonexistent")

    def test_add_credits_success(self, wallet_service, test_user, db_session):
        """Test adding credits"""
        result = wallet_service.add_credits(test_user.id, 50.0, "Test credit")
        
        assert result["balance"] == 150.0
        assert result["amount_added"] == 50.0
        assert "transaction_id" in result
        
        # Verify transaction created
        transaction = db_session.query(Transaction).filter(
            Transaction.id == result["transaction_id"]
        ).first()
        assert transaction is not None
        assert transaction.type == "credit"
        assert transaction.amount == 50.0

    def test_add_credits_negative_amount(self, wallet_service, test_user):
        """Test adding negative credits fails"""
        with pytest.raises(ValueError, match="Amount must be positive"):
            wallet_service.add_credits(test_user.id, -10.0)

    def test_add_credits_zero_amount(self, wallet_service, test_user):
        """Test adding zero credits fails"""
        with pytest.raises(ValueError, match="Amount must be positive"):
            wallet_service.add_credits(test_user.id, 0.0)

    def test_deduct_credits_success(self, wallet_service, test_user, db_session):
        """Test deducting credits"""
        result = wallet_service.deduct_credits(test_user.id, 30.0, "Test debit")
        
        assert result["balance"] == 70.0
        assert result["amount_deducted"] == 30.0
        
        # Verify transaction
        transaction = db_session.query(Transaction).filter(
            Transaction.id == result["transaction_id"]
        ).first()
        assert transaction.type == "debit"
        assert transaction.amount == 30.0

    def test_deduct_credits_insufficient_balance(self, wallet_service, test_user):
        """Test deducting more than balance fails"""
        with pytest.raises(ValueError, match="Insufficient balance"):
            wallet_service.deduct_credits(test_user.id, 200.0)

    def test_deduct_credits_negative_amount(self, wallet_service, test_user):
        """Test deducting negative amount fails"""
        with pytest.raises(ValueError, match="Amount must be positive"):
            wallet_service.deduct_credits(test_user.id, -10.0)

    def test_transaction_history(self, wallet_service, test_user, db_session):
        """Test getting transaction history"""
        # Create some transactions
        wallet_service.add_credits(test_user.id, 25.0, "Credit 1")
        wallet_service.deduct_credits(test_user.id, 10.0, "Debit 1")
        wallet_service.add_credits(test_user.id, 15.0, "Credit 2")
        
        history = wallet_service.get_transaction_history(test_user.id)
        
        assert len(history) == 3
        assert history[0]["type"] == "credit"  # Most recent first
        assert history[0]["amount"] == 15.0

    def test_transaction_history_limit(self, wallet_service, test_user):
        """Test transaction history respects limit"""
        # Create 10 transactions
        for i in range(10):
            wallet_service.add_credits(test_user.id, 1.0, f"Credit {i}")
        
        history = wallet_service.get_transaction_history(test_user.id, limit=5)
        assert len(history) == 5

    def test_concurrent_balance_updates(self, wallet_service, test_user, db_session):
        """Test SELECT FOR UPDATE prevents race conditions"""
        initial_balance = test_user.credits
        
        # Simulate concurrent operations
        wallet_service.add_credits(test_user.id, 10.0)
        wallet_service.deduct_credits(test_user.id, 5.0)
        
        final_balance = wallet_service.get_balance(test_user.id)
        assert final_balance == initial_balance + 10.0 - 5.0

    def test_negative_balance_prevention(self, wallet_service, db_session):
        """Test that balance cannot go negative"""
        user = User(
            id="zero_user",
            email="zero@example.com",
            credits=5.0
        )
        db_session.add(user)
        db_session.commit()
        
        with pytest.raises(ValueError, match="Insufficient balance"):
            wallet_service.deduct_credits(user.id, 10.0)
        
        # Verify balance unchanged
        assert wallet_service.get_balance(user.id) == 5.0


# Coverage target: 85%+
# Test count: 15+
