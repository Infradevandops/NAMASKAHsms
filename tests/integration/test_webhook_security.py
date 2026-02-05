"""Integration tests for webhook security."""
import pytest
import json
import hmac
import hashlib
from unittest.mock import patch

from app.core.config import get_settings


class TestWebhookSecurity:
    """Test webhook signature verification and security."""
    
    @pytest.mark.asyncio
    async def test_webhook_rejects_missing_signature(self, client):
        """Test webhook rejects requests without signature."""
        payload = {
            "event": "charge.success",
            "data": {
                "reference": "ref_test",
                "metadata": {"user_id": "user1", "namaskah_amount": 10.0}
            }
        }
        
        response = await client.post(
            "/api/wallet/paystack/webhook",
            json=payload
        )
        
        assert response.status_code == 401
        assert "signature" in response.json()["detail"].lower()
    
    @pytest.mark.asyncio
    async def test_webhook_rejects_invalid_signature(self, client):
        """Test webhook rejects requests with invalid signature."""
        payload = {
            "event": "charge.success",
            "data": {
                "reference": "ref_test",
                "metadata": {"user_id": "user1", "namaskah_amount": 10.0}
            }
        }
        
        response = await client.post(
            "/api/wallet/paystack/webhook",
            json=payload,
            headers={"x-paystack-signature": "invalid_signature"}
        )
        
        assert response.status_code == 401
        assert "signature" in response.json()["detail"].lower()
    
    @pytest.mark.asyncio
    async def test_webhook_accepts_valid_signature(self, client, db):
        """Test webhook accepts requests with valid signature."""
        from app.models.user import User
        from app.models.transaction import PaymentLog
        
        # Create user and payment log
        user = User(email="test@test.com", credits=0.0)
        db.add(user)
        db.commit()
        
        log = PaymentLog(
            user_id=user.id,
            email=user.email,
            reference="ref_valid",
            amount_usd=10.0,
            state="processing",
            credited=False
        )
        db.add(log)
        db.commit()
        
        payload = {
            "event": "charge.success",
            "data": {
                "reference": "ref_valid",
                "metadata": {"user_id": user.id, "namaskah_amount": 10.0}
            }
        }
        
        # Generate valid signature
        settings = get_settings()
        body = json.dumps(payload).encode('utf-8')
        signature = hmac.new(
            settings.paystack_secret_key.encode('utf-8'),
            body,
            hashlib.sha512
        ).hexdigest()
        
        response = await client.post(
            "/api/wallet/paystack/webhook",
            json=payload,
            headers={"x-paystack-signature": signature}
        )
        
        assert response.status_code == 200
        assert response.json()["status"] == "success"
    
    @pytest.mark.asyncio
    async def test_webhook_requires_reference(self, client):
        """Test webhook requires reference in payload."""
        settings = get_settings()
        payload = {
            "event": "charge.success",
            "data": {
                "metadata": {"user_id": "user1", "namaskah_amount": 10.0}
            }
        }
        
        body = json.dumps(payload).encode('utf-8')
        signature = hmac.new(
            settings.paystack_secret_key.encode('utf-8'),
            body,
            hashlib.sha512
        ).hexdigest()
        
        response = await client.post(
            "/api/wallet/paystack/webhook",
            json=payload,
            headers={"x-paystack-signature": signature}
        )
        
        assert response.status_code == 400
        assert "reference" in response.json()["detail"].lower()
    
    @pytest.mark.asyncio
    async def test_webhook_uses_distributed_lock(self, client, db, cache):
        """Test webhook uses distributed lock for processing."""
        from app.models.user import User
        from app.models.transaction import PaymentLog
        
        user = User(email="test@test.com", credits=0.0)
        db.add(user)
        db.commit()
        
        log = PaymentLog(
            user_id=user.id,
            email=user.email,
            reference="ref_lock",
            amount_usd=10.0,
            state="processing",
            credited=False
        )
        db.add(log)
        db.commit()
        
        settings = get_settings()
        payload = {
            "event": "charge.success",
            "data": {
                "reference": "ref_lock",
                "metadata": {"user_id": user.id, "namaskah_amount": 10.0}
            }
        }
        
        body = json.dumps(payload).encode('utf-8')
        signature = hmac.new(
            settings.paystack_secret_key.encode('utf-8'),
            body,
            hashlib.sha512
        ).hexdigest()
        
        # Acquire lock manually
        redis = cache
        lock = redis.lock("payment_lock:ref_lock", timeout=30)
        lock.acquire()
        
        try:
            # Webhook should timeout trying to acquire lock
            response = await client.post(
                "/api/wallet/paystack/webhook",
                json=payload,
                headers={"x-paystack-signature": signature}
            )
            
            assert response.status_code == 500
        finally:
            lock.release()


class TestWebhookRetry:
    """Test webhook retry logic."""
    
    @pytest.mark.asyncio
    async def test_retry_on_failure(self, db):
        """Test webhook retries on failure."""
        from app.services.payment_service import PaymentService
        from app.models.user import User
        from app.models.transaction import PaymentLog
        
        user = User(email="test@test.com", credits=0.0)
        db.add(user)
        db.commit()
        
        log = PaymentLog(
            user_id=user.id,
            email=user.email,
            reference="ref_retry",
            amount_usd=10.0,
            state="processing",
            credited=False
        )
        db.add(log)
        db.commit()
        
        service = PaymentService(db)
        
        # Mock credit_user_with_lock to fail twice then succeed
        call_count = 0
        original_method = service.credit_user_with_lock
        
        async def mock_credit(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise Exception("Temporary failure")
            return await original_method(*args, **kwargs)
        
        service.credit_user_with_lock = mock_credit
        
        # Should succeed after retries
        result = await service.process_webhook_with_retry(user.id, 10.0, "ref_retry")
        
        assert result is True
        assert call_count == 3
    
    @pytest.mark.asyncio
    async def test_dead_letter_queue_on_max_retries(self, db):
        """Test failed webhooks logged to dead letter queue."""
        from app.services.payment_service import PaymentService
        from app.models.user import User
        from app.models.transaction import PaymentLog
        
        user = User(email="test@test.com", credits=0.0)
        db.add(user)
        db.commit()
        
        log = PaymentLog(
            user_id=user.id,
            email=user.email,
            reference="ref_dlq",
            amount_usd=10.0,
            state="processing",
            credited=False
        )
        db.add(log)
        db.commit()
        
        service = PaymentService(db)
        
        # Mock to always fail
        async def mock_credit(*args, **kwargs):
            raise Exception("Permanent failure")
        
        service.credit_user_with_lock = mock_credit
        
        # Should fail after max retries
        with pytest.raises(Exception, match="Permanent failure"):
            await service.process_webhook_with_retry(user.id, 10.0, "ref_dlq", max_retries=3)
        
        # Check dead letter queue
        db.refresh(log)
        assert log.state == "failed"
        assert "Webhook processing failed" in log.error_message
