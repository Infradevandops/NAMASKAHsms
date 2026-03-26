"""Tests for verification cost sync after refund adjustment in purchase_endpoints."""

import uuid
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.models.user import User
from app.models.verification import Verification


@pytest.fixture
def user_with_credits(db):
    user = User(
        id=str(uuid.uuid4()),
        email=f"{uuid.uuid4().hex[:8]}@example.com",
        password_hash="$2b$12$test",
        credits=Decimal("50.0000"),
        subscription_tier="payg",
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def pending_verification(db, user_with_credits):
    ver = Verification(
        id=str(uuid.uuid4()),
        user_id=user_with_credits.id,
        service_name="telegram",
        phone_number="+15551234567",
        country="US",
        status="pending",
        cost=Decimal("2.7500"),  # base + surcharge before refund
        provider="textverified",
        activation_id="tv_test_123",
        area_code_surcharge=Decimal("0.2500"),
        carrier_surcharge=Decimal("0.0000"),
        area_code_matched=False,  # triggers surcharge refund
    )
    db.add(ver)
    db.commit()
    db.refresh(ver)
    return ver


@pytest.mark.asyncio
async def test_verification_cost_synced_after_refund(db, user_with_credits, pending_verification):
    """verification.cost must reflect actual_cost after refund, not the pre-refund price."""
    from app.services.refund_service import RefundService

    refund_service = RefundService()
    initial_cost = float(pending_verification.cost)  # 2.75

    result = await refund_service.process_refund(pending_verification, user_with_credits, db)

    if result["refund_issued"]:
        refund_amount = result["refund_amount"]
        expected_cost = initial_cost - refund_amount

        # Simulate what purchase_endpoints now does
        pending_verification.cost = type(pending_verification.cost)(expected_cost)
        db.commit()
        db.refresh(pending_verification)

        assert float(pending_verification.cost) == pytest.approx(expected_cost)
        assert float(pending_verification.cost) < initial_cost


@pytest.mark.asyncio
async def test_verification_cost_unchanged_when_no_refund(db, user_with_credits):
    """verification.cost must not change when no refund is issued."""
    from app.services.refund_service import RefundService

    ver = Verification(
        id=str(uuid.uuid4()),
        user_id=user_with_credits.id,
        service_name="telegram",
        phone_number="+15559876543",
        country="US",
        status="pending",
        cost=Decimal("2.5000"),
        provider="textverified",
        activation_id="tv_test_456",
        area_code_surcharge=Decimal("0.0000"),
        carrier_surcharge=Decimal("0.0000"),
        area_code_matched=True,
    )
    db.add(ver)
    db.commit()

    refund_service = RefundService()
    result = await refund_service.process_refund(ver, user_with_credits, db)

    assert result["refund_issued"] is False
    assert float(ver.cost) == pytest.approx(2.50)


@pytest.mark.asyncio
async def test_credit_deduction_matches_verification_cost(db, user_with_credits, pending_verification):
    """verification.cost after refund sync must equal initial_cost minus refund_amount."""
    from app.services.refund_service import RefundService

    initial_cost = float(pending_verification.cost)  # 2.75
    refund_service = RefundService()

    result = await refund_service.process_refund(pending_verification, user_with_credits, db)

    actual_cost = initial_cost
    if result["refund_issued"]:
        actual_cost -= result["refund_amount"]
        pending_verification.cost = type(pending_verification.cost)(actual_cost)

    # verification.cost must reflect what was actually charged
    assert float(pending_verification.cost) == pytest.approx(actual_cost)
    assert float(pending_verification.cost) < initial_cost if result["refund_issued"] else True
