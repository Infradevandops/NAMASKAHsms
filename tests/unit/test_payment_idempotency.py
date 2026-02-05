"""Unit tests for payment idempotency."""
import pytest
from unittest.mock import Mock, patch
from datetime import datetime

from app.services.payment_service import PaymentService
from app.models.transaction import PaymentLog


class TestIdempotencyGuard:
    """Test idempotency guard functionality."""
    
    def test_check_idempotency_returns_none_when_not_found(self, db):
        """Test idempotency check returns None when key not found."""
        service = PaymentService(db)
        result = service._check_idempotency("nonexistent_key")
        assert result is None
    
    def test_check_idempotency_returns_cached_when_completed(self, db):
        """Test idempotency check returns cached result when completed."""
        log = PaymentLog(
            user_id="user1",
            email="test@test.com",
            reference="ref_123",
            amount_usd=10.0,
            state="completed",
            idempotency_key="idem_key_123"
        )
        db.add(log)
        db.commit()
        
        service = PaymentService(db)
        result = service._check_idempotency("idem_key_123")
        
        assert result is not None
        assert result["cached"] is True
        assert result["reference"] == "ref_123"
    
    def test_check_idempotency_returns_none_when_pending(self, db):
        """Test idempotency check returns None when payment pending."""
        log = PaymentLog(
            user_id="user1",
            email="test@test.com",
            reference="ref_456",
            amount_usd=10.0,
            state="pending",
            idempotency_key="idem_key_456"
        )
        db.add(log)
        db.commit()
        
        service = PaymentService(db)
        result = service._check_idempotency("idem_key_456")
        
        assert result is None
    
    @pytest.mark.asyncio
    async def test_initialize_payment_returns_cached_result(self, db):
        """Test initialize_payment returns cached result for duplicate request."""
        log = PaymentLog(
            user_id="user1",
            email="test@test.com",
            reference="ref_789",
            amount_usd=10.0,
            state="completed",
            idempotency_key="idem_key_789"
        )
        db.add(log)
        db.commit()
        
        service = PaymentService(db)
        result = await service.initialize_payment(
            user_id="user1",
            email="test@test.com",
            amount_usd=10.0,
            idempotency_key="idem_key_789"
        )
        
        assert result["cached"] is True
        assert result["reference"] == "ref_789"
    
    @pytest.mark.asyncio
    @patch('requests.post')
    async def test_initialize_payment_creates_payment_log(self, mock_post, db):
        """Test initialize_payment creates PaymentLog with pending state."""
        mock_post.return_value = Mock(
            status_code=200,
            json=lambda: {
                "status": True,
                "data": {
                    "reference": "ref_new",
                    "authorization_url": "https://checkout.paystack.com/test",
                    "access_code": "test_code"
                }
            }
        )
        
        service = PaymentService(db)
        result = await service.initialize_payment(
            user_id="user1",
            email="test@test.com",
            amount_usd=10.0,
            idempotency_key="idem_new"
        )
        
        # Check PaymentLog was created
        log = db.query(PaymentLog).filter(
            PaymentLog.idempotency_key == "idem_new"
        ).first()
        
        assert log is not None
        assert log.state == "processing"
        assert log.idempotency_key == "idem_new"


class TestRaceConditionProtection:
    """Test race condition protection in credit_user."""
    
    def test_credit_user_prevents_double_credit(self, db):
        """Test credit_user prevents double crediting."""
        from app.models.user import User
        user = User(email="test@test.com", credits=0.0)
        db.add(user)
        db.commit()
        
        log = PaymentLog(
            user_id=user.id,
            email=user.email,
            reference="ref_double",
            amount_usd=10.0,
            state="completed",
            credited=True
        )
        db.add(log)
        db.commit()
        
        service = PaymentService(db)
        result = service.credit_user(user.id, 10.0, "ref_double")
        
        assert result is True
        # User should not be credited again
        db.refresh(user)
        assert user.credits == 0.0  # Initial value
    
    def test_credit_user_updates_payment_log_state(self, db):
        """Test credit_user updates PaymentLog state to completed."""
        from app.models.user import User
        user = User(email="test@test.com", credits=0.0)
        db.add(user)
        db.commit()
        
        log = PaymentLog(
            user_id=user.id,
            email=user.email,
            reference="ref_state",
            amount_usd=10.0,
            state="processing",
            credited=False
        )
        db.add(log)
        db.commit()
        
        service = PaymentService(db)
        service.credit_user(user.id, 10.0, "ref_state")
        
        db.refresh(log)
        assert log.state == "completed"
        assert log.credited is True
        assert log.processing_completed_at is not None
    
    def test_credit_user_creates_transaction_record(self, db):
        """Test credit_user creates Transaction record."""
        from app.models.user import User
        user = User(email="test@test.com", credits=0.0)
        db.add(user)
        db.commit()
        
        log = PaymentLog(
            user_id=user.id,
            email=user.email,
            reference="ref_txn",
            amount_usd=10.0,
            state="processing",
            credited=False
        )
        db.add(log)
        db.commit()
        
        service = PaymentService(db)
        service.credit_user(user.id, 10.0, "ref_txn")
        
        from app.models.transaction import Transaction
        txn = db.query(Transaction).filter(
            Transaction.reference == "ref_txn"
        ).first()
        
        assert txn is not None
        assert txn.amount == 10.0
        assert txn.type == "credit"
        assert txn.payment_log_id == log.id
    
    def test_credit_user_raises_on_missing_payment_log(self, db):
        """Test credit_user raises error when PaymentLog not found."""
        from app.models.user import User
        user = User(email="test@test.com", credits=0.0)
        db.add(user)
        db.commit()
        
        service = PaymentService(db)
        
        with pytest.raises(ValueError, match="Payment log .* not found"):
            service.credit_user(user.id, 10.0, "nonexistent_ref")
    
    def test_credit_user_raises_on_missing_user(self, db):
        """Test credit_user raises error when User not found."""
        log = PaymentLog(
            user_id="nonexistent_user",
            email="test@test.com",
            reference="ref_nouser",
            amount_usd=10.0,
            state="processing",
            credited=False
        )
        db.add(log)
        db.commit()
        
        service = PaymentService(db)
        
        with pytest.raises(ValueError, match="User .* not found"):
            service.credit_user("nonexistent_user", 10.0, "ref_nouser")
