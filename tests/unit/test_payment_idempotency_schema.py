"""Unit tests for payment idempotency schema."""
import pytest
from datetime import datetime
from sqlalchemy.exc import IntegrityError

from app.models.transaction import Transaction, PaymentLog


class TestTransactionIdempotency:
    """Test Transaction model idempotency fields."""
    
    def test_reference_unique_constraint(self, db):
        """Test reference field enforces uniqueness."""
        ref = "test_ref_123"
        
        t1 = Transaction(user_id="user1", amount=10.0, type="credit", reference=ref)
        db.add(t1)
        db.commit()
        
        t2 = Transaction(user_id="user2", amount=20.0, type="credit", reference=ref)
        db.add(t2)
        
        with pytest.raises(IntegrityError):
            db.commit()
    
    def test_idempotency_key_unique_constraint(self, db):
        """Test idempotency_key field enforces uniqueness."""
        key = "idem_key_123"
        
        t1 = Transaction(user_id="user1", amount=10.0, type="credit", idempotency_key=key)
        db.add(t1)
        db.commit()
        
        t2 = Transaction(user_id="user2", amount=20.0, type="credit", idempotency_key=key)
        db.add(t2)
        
        with pytest.raises(IntegrityError):
            db.commit()
    
    def test_payment_log_linking(self, db):
        """Test transaction can link to payment log."""
        log = PaymentLog(
            user_id="user1",
            email="test@test.com",
            reference="ref_123",
            amount_usd=10.0,
            state="completed"
        )
        db.add(log)
        db.commit()
        
        txn = Transaction(
            user_id="user1",
            amount=10.0,
            type="credit",
            payment_log_id=log.id
        )
        db.add(txn)
        db.commit()
        
        assert txn.payment_log_id == log.id


class TestPaymentLogStateMachine:
    """Test PaymentLog state machine fields."""
    
    def test_default_state_is_pending(self, db):
        """Test new payment logs default to pending state."""
        log = PaymentLog(
            user_id="user1",
            email="test@test.com",
            reference="ref_default_123",
            amount_usd=10.0
        )
        db.add(log)
        db.commit()
        
        assert log.state == "pending"
    
    def test_state_transitions_tracking(self, db):
        """Test state transitions are tracked."""
        log = PaymentLog(
            user_id="user1",
            email="test@test.com",
            reference="ref_transitions_123",
            amount_usd=10.0,
            state="pending",
            state_transitions=[
                {"from": None, "to": "pending", "at": datetime.utcnow().isoformat()}
            ]
        )
        db.add(log)
        db.commit()
        
        assert len(log.state_transitions) == 1
        assert log.state_transitions[0]["to"] == "pending"
    
    def test_processing_timestamps(self, db):
        """Test processing timestamps are recorded."""
        now = datetime.utcnow()
        log = PaymentLog(
            user_id="user1",
            email="test@test.com",
            reference="ref_timestamps_123",
            amount_usd=10.0,
            processing_started_at=now
        )
        db.add(log)
        db.commit()
        
        assert log.processing_started_at == now
    
    def test_lock_version_default(self, db):
        """Test lock_version defaults to 0."""
        log = PaymentLog(
            user_id="user1",
            email="test@test.com",
            reference="ref_lock_123",
            amount_usd=10.0
        )
        db.add(log)
        db.commit()
        
        assert log.lock_version == 0
    
    def test_idempotency_key_unique(self, db):
        """Test idempotency_key enforces uniqueness."""
        key = "idem_key_456"
        
        log1 = PaymentLog(
            user_id="user1",
            email="test1@test.com",
            reference="ref_1",
            amount_usd=10.0,
            idempotency_key=key
        )
        db.add(log1)
        db.commit()
        
        log2 = PaymentLog(
            user_id="user2",
            email="test2@test.com",
            reference="ref_2",
            amount_usd=20.0,
            idempotency_key=key
        )
        db.add(log2)
        
        with pytest.raises(IntegrityError):
            db.commit()
    
    def test_state_values(self, db):
        """Test valid state values."""
        states = ["pending", "processing", "completed", "failed", "refunded"]
        
        for state in states:
            log = PaymentLog(
                user_id="user1",
                email="test@test.com",
                reference=f"ref_{state}",
                amount_usd=10.0,
                state=state
            )
            db.add(log)
            db.commit()
            
            assert log.state == state
            db.rollback()
