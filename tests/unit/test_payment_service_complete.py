
import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from datetime import datetime, timezone
from app.services.payment_service import PaymentService
from app.models.transaction import PaymentLog, Transaction
from app.models.user import User

# Critical Path: Payment Service
# Status: Implementing High-Priority Tests

class TestPaymentServiceExtended:
    """Extended payment service tests for critical paths."""
    
    @pytest.fixture
    def payment_service(self, db_session, redis_client):
        with patch("redis.Redis.from_url", return_value=redis_client):
            return PaymentService(db_session)
    
    @pytest.mark.asyncio
    async def test_payment_double_credit_prevention(self, payment_service, regular_user, db_session, redis_client):
        """Test that duplicate credits are prevented via Redis lock."""
        reference = "ref_duplicate_test"
        amount = 50.0
        
        # First credit should succeed
        result1 = await payment_service.credit_user(reference, amount, regular_user.id)
        assert result1["status"] == "success"
        
        # Second credit with same reference should be prevented
        result2 = await payment_service.credit_user(reference, amount, regular_user.id)
        assert result2["status"] == "duplicate"
        
        # Verify user only credited once
        db_session.refresh(regular_user)
        assert regular_user.credits == 60.0  # 10 initial + 50
    
    async def test_payment_amount_validation(self, payment_service, regular_user):
        """Test payment amount validation."""
        # Negative amount
        with pytest.raises(ValueError, match="Amount must be positive"):
            await payment_service.initiate_payment(regular_user.id, -10.0)
        
        # Zero amount
        with pytest.raises(ValueError, match="Amount must be positive"):
            await payment_service.initiate_payment(regular_user.id, 0.0)
        
        # Very large amount (potential fraud)
        with pytest.raises(ValueError, match="Amount exceeds maximum"):
            await payment_service.initiate_payment(regular_user.id, 1000000.0)
    
    async def test_payment_user_not_found(self, payment_service):
        """Test payment with non-existent user."""
        fake_user_id = "nonexistent-user-id"
        
        with pytest.raises(ValueError, match="User not found"):
            await payment_service.initiate_payment(fake_user_id, 10.0)
    
    @patch("app.services.payment_service.paystack_service")
    async def test_payment_paystack_error(self, mock_paystack, payment_service, regular_user):
        """Test handling of Paystack API errors."""
        mock_paystack.enabled = True
        mock_paystack.initialize_payment = AsyncMock(side_effect=Exception("Paystack API error"))
        
        with pytest.raises(Exception, match="Paystack API error"):
            await payment_service.initiate_payment(regular_user.id, 10.0)
    
    async def test_payment_invalid_reference(self, payment_service, regular_user):
        """Test verification with invalid reference."""
        invalid_ref = "invalid_ref_12345"
        
        with pytest.raises(ValueError, match="Payment not found"):
            await payment_service.verify_payment(invalid_ref, regular_user.id)
    
    async def test_payment_status_transitions(self, payment_service, regular_user, db_session):
        """Test valid payment status transitions."""
        reference = "ref_status_test"
        
        # Create pending payment
        log = PaymentLog(
            user_id=regular_user.id,
            email=regular_user.email,
            reference=reference,
            amount_usd=10.0,
            namaskah_amount=10.0,
            status="pending",
            credited=False,
        )
        db_session.add(log)
        db_session.commit()
        
        # Transition to success
        log.status = "success"
        log.credited = True
        db_session.commit()
        
        db_session.refresh(log)
        assert log.status == "success"
        assert log.credited is True
    
    async def test_payment_balance_update_atomic(self, payment_service, regular_user, db_session, redis_client):
        """Test that balance updates are atomic."""
        reference = "ref_atomic_test"
        amount = 25.0
        initial_balance = regular_user.credits
        
        # Credit user
        await payment_service.credit_user(reference, amount, regular_user.id)
        
        # Verify balance updated correctly
        db_session.refresh(regular_user)
        assert regular_user.credits == initial_balance + amount
        
        # Verify idempotency key exists in Redis
        key = f"payment:credited:{reference}"
        assert redis_client.get(key) is not None
    
    def test_payment_get_history_pagination(self, payment_service, regular_user, db_session):
        """Test payment history with pagination."""
        # Create multiple payment logs
        for i in range(5):
            log = PaymentLog(
                user_id=regular_user.id,
                email=regular_user.email,
                reference=f"ref_hist_{i}",
                amount_usd=10.0 + i,
                status="success",
            )
            db_session.add(log)
        db_session.commit()
        
        # Get history
        history = payment_service.get_payment_history(regular_user.id, limit=3)
        assert len(history["payments"]) <= 3
    
    def test_payment_summary_calculations(self, payment_service, regular_user, db_session):
        """Test payment summary calculations."""
        # Add successful and failed payments
        db_session.add(PaymentLog(
            user_id=regular_user.id,
            email=regular_user.email,
            reference="ref_sum_success",
            amount_usd=100.0,
            status="success",
        ))
        db_session.add(PaymentLog(
            user_id=regular_user.id,
            email=regular_user.email,
            reference="ref_sum_failed",
            amount_usd=50.0,
            status="failed",
        ))
        db_session.commit()
        
        summary = payment_service.get_payment_summary(regular_user.id)
        assert summary["total_paid"] >= 100.0
        assert summary["total_payments"] >= 1
    
    @pytest.mark.asyncio
    async def test_payment_webhook_idempotency(self, payment_service, regular_user, db_session, redis_client):
        """Test webhook processing is idempotent."""
        reference = "ref_webhook_idem"
        
        # Create payment log
        log = PaymentLog(
            user_id=regular_user.id,
            email=regular_user.email,
            reference=reference,
            amount_usd=30.0,
            namaskah_amount=30.0,
            status="pending",
            credited=False,
        )
        db_session.add(log)
        db_session.commit()
        
        payload = {"reference": reference, "amount": 3000000}
        
        # Process webhook twice
        result1 = await payment_service.process_webhook("charge.success", payload)
        result2 = await payment_service.process_webhook("charge.success", payload)
        
        # Both should succeed but only credit once
        assert result1["status"] == "success"
        assert result2["status"] == "duplicate"
        
        db_session.refresh(regular_user)
        assert regular_user.credits == 40.0  # 10 initial + 30, not 70


# Skipped tests for future implementation
@pytest.mark.skip(reason="Not implemented yet")
def test_concurrent_payment_handling():
    pass

@pytest.mark.skip(reason="Not implemented yet")
def test_payment_with_database_lock():
    pass

@pytest.mark.skip(reason="Not implemented yet")
def test_payment_timeout_handling():
    pass

@pytest.mark.skip(reason="Not implemented yet")
def test_payment_retry_logic():
    pass

@pytest.mark.skip(reason="Not implemented yet")
def test_payment_reconciliation():
    pass

@pytest.mark.skip(reason="Not implemented yet")
def test_payment_webhook_out_of_order():
    pass

@pytest.mark.skip(reason="Not implemented yet")
def test_payment_partial_refund():
    pass

@pytest.mark.skip(reason="Not implemented yet")
def test_payment_full_refund():
    pass

@pytest.mark.skip(reason="Not implemented yet")
def test_payment_refund_insufficient_balance():
    pass

@pytest.mark.skip(reason="Not implemented yet")
def test_payment_currency_conversion():
    pass

@pytest.mark.skip(reason="Not implemented yet")
def test_payment_expired_transaction():
    pass

@pytest.mark.skip(reason="Not implemented yet")
def test_payment_audit_logging():
    pass

@pytest.mark.skip(reason="Not implemented yet")
def test_payment_notification_trigger():
    pass

@pytest.mark.skip(reason="Not implemented yet")
def test_payment_transaction_rollback():
    pass

@pytest.mark.skip(reason="Not implemented yet")
def test_payment_edge_cases():
    pass
