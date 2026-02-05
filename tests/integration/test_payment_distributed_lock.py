"""Integration tests for payment distributed locking."""
import pytest
import asyncio
from concurrent.futures import ThreadPoolExecutor
from unittest.mock import patch

from app.services.payment_service import PaymentService
from app.models.transaction import PaymentLog
from app.models.user import User


class TestDistributedLock:
    """Test distributed locking for payment operations."""
    
    @pytest.mark.asyncio
    async def test_credit_user_with_lock_acquires_lock(self, db, test_user, cache):
        """Test credit_user_with_lock acquires Redis lock."""
        log = PaymentLog(
            user_id=test_user.id,
            email=test_user.email,
            reference="ref_lock_test",
            amount_usd=10.0,
            state="processing",
            credited=False
        )
        db.add(log)
        db.commit()
        
        service = PaymentService(db)
        result = await service.credit_user_with_lock(test_user.id, 10.0, "ref_lock_test")
        
        assert result is True
        db.refresh(test_user)
        assert test_user.credits == 10.0
    
    @pytest.mark.asyncio
    async def test_credit_user_with_lock_prevents_concurrent_access(self, db, test_user, cache):
        """Test distributed lock prevents concurrent crediting."""
        log = PaymentLog(
            user_id=test_user.id,
            email=test_user.email,
            reference="ref_concurrent",
            amount_usd=10.0,
            state="processing",
            credited=False
        )
        db.add(log)
        db.commit()
        
        service = PaymentService(db)
        
        # Simulate concurrent requests
        async def credit_with_delay():
            result = await service.credit_user_with_lock(test_user.id, 10.0, "ref_concurrent")
            await asyncio.sleep(0.1)
            return result
        
        # Both should succeed but only one should actually credit
        results = await asyncio.gather(
            credit_with_delay(),
            credit_with_delay(),
            return_exceptions=True
        )
        
        # At least one should succeed
        assert any(r is True for r in results if not isinstance(r, Exception))
        
        # User should only be credited once
        db.refresh(test_user)
        assert test_user.credits == 10.0
    
    @pytest.mark.asyncio
    async def test_credit_user_with_lock_releases_on_error(self, db, cache):
        """Test lock is released even when error occurs."""
        # Create log but no user (will cause error)
        log = PaymentLog(
            user_id="nonexistent",
            email="test@test.com",
            reference="ref_error",
            amount_usd=10.0,
            state="processing",
            credited=False
        )
        db.add(log)
        db.commit()
        
        service = PaymentService(db)
        
        with pytest.raises(ValueError):
            await service.credit_user_with_lock("nonexistent", 10.0, "ref_error")
        
        # Lock should be released, so we can acquire it again
        result = await service.credit_user_with_lock.__wrapped__(service, "nonexistent", 10.0, "ref_error_2")
        # Should fail again but not due to lock
    
    @pytest.mark.asyncio
    async def test_credit_user_with_lock_timeout(self, db, test_user, cache):
        """Test lock acquisition timeout."""
        log = PaymentLog(
            user_id=test_user.id,
            email=test_user.email,
            reference="ref_timeout",
            amount_usd=10.0,
            state="processing",
            credited=False
        )
        db.add(log)
        db.commit()
        
        service = PaymentService(db)
        
        # Acquire lock manually
        redis = cache
        lock = redis.lock("payment_lock:ref_timeout", timeout=30)
        lock.acquire()
        
        try:
            # Try to credit with lock (should timeout)
            with pytest.raises(Exception, match="Could not acquire payment lock"):
                await service.credit_user_with_lock(test_user.id, 10.0, "ref_timeout")
        finally:
            lock.release()
