"""
Test refund policy enforcer to ensure it works in production
"""

import asyncio
import pytest
from datetime import datetime, timedelta, timezone
from decimal import Decimal

from app.models.verification import Verification
from app.models.user import User
from app.services.refund_policy_enforcer import RefundPolicyEnforcer


@pytest.mark.asyncio
async def test_refund_enforcer_finds_stuck_verifications(db_session):
    """Test that enforcer finds and refunds stuck verifications."""
    # Create user
    user = User(
        email="test@example.com",
        hashed_password="test",
        subscription_tier="payg",
        credits=Decimal("10.00"),
    )
    db_session.add(user)
    db_session.commit()

    # Create stuck verification (>10 minutes old, still pending)
    stuck_verification = Verification(
        user_id=user.id,
        service_name="whatsapp",
        phone_number="+12025551234",
        status="pending",
        cost=Decimal("2.50"),
        created_at=datetime.now(timezone.utc) - timedelta(minutes=15),
        activation_id="test_activation_123",
    )
    db_session.add(stuck_verification)
    db_session.commit()

    initial_balance = user.credits

    # Run enforcer
    enforcer = RefundPolicyEnforcer()
    await enforcer._enforce_refund_policy()

    # Refresh from DB
    db_session.refresh(user)
    db_session.refresh(stuck_verification)

    # Verify refund processed
    assert stuck_verification.status == "timeout"
    assert stuck_verification.refunded == True
    assert user.credits == initial_balance + Decimal("2.50")


@pytest.mark.asyncio
async def test_refund_enforcer_handles_failed_verifications(db_session):
    """Test that enforcer refunds failed verifications."""
    # Create user
    user = User(
        email="test2@example.com",
        hashed_password="test",
        subscription_tier="custom",
        credits=Decimal("5.00"),
    )
    db_session.add(user)
    db_session.commit()

    # Create failed verification (not refunded yet)
    failed_verification = Verification(
        user_id=user.id,
        service_name="telegram",
        phone_number="+12025551235",
        status="failed",
        cost=Decimal("0.20"),
        created_at=datetime.now(timezone.utc) - timedelta(minutes=5),
        activation_id="test_activation_456",
        refunded=False,
    )
    db_session.add(failed_verification)
    db_session.commit()

    initial_balance = user.credits

    # Run enforcer
    enforcer = RefundPolicyEnforcer()
    await enforcer._enforce_refund_policy()

    # Refresh from DB
    db_session.refresh(user)
    db_session.refresh(failed_verification)

    # Verify refund processed
    assert failed_verification.refunded == True
    assert user.credits == initial_balance + Decimal("0.20")


@pytest.mark.asyncio
async def test_refund_enforcer_skips_already_refunded(db_session):
    """Test that enforcer doesn't double-refund."""
    # Create user
    user = User(
        email="test3@example.com",
        hashed_password="test",
        subscription_tier="pro",
        credits=Decimal("15.00"),
    )
    db_session.add(user)
    db_session.commit()

    # Create already-refunded verification
    refunded_verification = Verification(
        user_id=user.id,
        service_name="discord",
        phone_number="+12025551236",
        status="timeout",
        cost=Decimal("0.30"),
        created_at=datetime.now(timezone.utc) - timedelta(minutes=20),
        activation_id="test_activation_789",
        refunded=True,
    )
    db_session.add(refunded_verification)
    db_session.commit()

    initial_balance = user.credits

    # Run enforcer
    enforcer = RefundPolicyEnforcer()
    await enforcer._enforce_refund_policy()

    # Refresh from DB
    db_session.refresh(user)

    # Verify no double refund
    assert user.credits == initial_balance


@pytest.mark.asyncio
async def test_refund_enforcer_immediate_enforcement(db_session):
    """Test immediate enforcement for single verification."""
    # Create user
    user = User(
        email="test4@example.com",
        hashed_password="test",
        subscription_tier="payg",
        credits=Decimal("2.40"),
    )
    db_session.add(user)
    db_session.commit()

    # Create timeout verification
    timeout_verification = Verification(
        user_id=user.id,
        service_name="whatsapp",
        phone_number="+12025551237",
        status="timeout",
        cost=Decimal("2.50"),
        created_at=datetime.now(timezone.utc),
        activation_id="test_activation_999",
        refunded=False,
    )
    db_session.add(timeout_verification)
    db_session.commit()

    initial_balance = user.credits

    # Run immediate enforcement
    enforcer = RefundPolicyEnforcer()
    result = await enforcer.enforce_single_verification(
        timeout_verification.id, db_session
    )

    # Verify refund processed
    assert result is not None
    assert result["refund_amount"] == 2.50

    # Refresh from DB
    db_session.refresh(user)
    db_session.refresh(timeout_verification)

    assert timeout_verification.refunded == True
    assert user.credits == initial_balance + Decimal("2.50")


def test_refund_enforcer_configuration():
    """Test enforcer configuration."""
    enforcer = RefundPolicyEnforcer()

    assert enforcer.enforcement_interval == 300  # 5 minutes
    assert enforcer.timeout_threshold == 600  # 10 minutes
    assert enforcer.is_running == False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
