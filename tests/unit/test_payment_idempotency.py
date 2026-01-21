"""Test payment idempotency."""

import asyncio
from unittest.mock import Mock

import pytest

from app.models.user import User
from app.services.payment_service import PaymentService


@pytest.mark.asyncio
async def test_duplicate_payment_prevented(db_session, redis_client):
    """Test that duplicate payments are prevented."""
    service = PaymentService(db_session, redis_client)

    # First credit
    # We need to mock the user
    user = User(id="user1", email="test@example.com", credits=0.0)
    db_session.add(user)
    db_session.commit()

    result1 = await service.credit_user("ref123", 10.0, "user1")
    assert result1["status"] == "success"

    # Duplicate credit attempt
    result2 = await service.credit_user("ref123", 10.0, "user1")
    assert result2["status"] == "duplicate"

    # Verify user only credited once
    user = db_session.query(User).filter(User.id == "user1").first()
    assert user.credits == 10.0


@pytest.mark.asyncio
async def test_concurrent_payment_handling(db_session, redis_client):
    """Test concurrent payment attempts."""
    service = PaymentService(db_session, redis_client)

    user = User(id="user2", email="test2@example.com", credits=0.0)
    db_session.add(user)
    db_session.commit()

    # Simulate concurrent requests
    tasks = [service.credit_user("ref456", 5.0, "user2") for _ in range(10)]

    results = await asyncio.gather(*tasks, return_exceptions=True)

    # Only one should succeed
    success_count = sum(
        1 for r in results if isinstance(r, dict) and r["status"] == "success"
    )
    assert success_count == 1
