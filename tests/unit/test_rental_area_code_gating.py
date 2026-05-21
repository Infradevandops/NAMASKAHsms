"""Test rental area code tier gating."""

import pytest
from sqlalchemy.orm import Session

from app.models.subscription_tier import SubscriptionTier
from app.models.user import User
from app.services.pricing_calculator import PricingCalculator


@pytest.fixture
def setup_tiers(db: Session):
    """Setup tier configurations."""
    tiers = [
        SubscriptionTier(
            tier="freemium", name="Freemium", has_area_code_selection=False
        ),
        SubscriptionTier(
            tier="payg", name="Pay-As-You-Go", has_area_code_selection=True
        ),
        SubscriptionTier(tier="pro", name="Pro", has_area_code_selection=True),
        SubscriptionTier(tier="custom", name="Custom", has_area_code_selection=True),
    ]
    for tier in tiers:
        db.add(tier)
    db.commit()


def test_freemium_blocked_from_rental_area_code(db: Session, setup_tiers):
    """Freemium users cannot use area code selection for rentals."""
    user = User(
        id="user1",
        email="user1@test.com",
        password_hash="test",
        subscription_tier="freemium",
        credits=10.0,
    )
    db.add(user)
    db.commit()

    with pytest.raises(
        ValueError, match="Area code selection not available for Freemium tier"
    ):
        PricingCalculator.calculate_rental_cost(
            db, "user1", duration_hours=24, provider_cost=5.0, area_code="212"
        )


def test_payg_charges_rental_area_code_fee(db: Session, setup_tiers):
    """PAYG users pay $0.50 for rental area code selection."""
    user = User(
        id="user2",
        email="user2@test.com",
        password_hash="test",
        subscription_tier="payg",
        credits=10.0,
    )
    db.add(user)
    db.commit()

    result = PricingCalculator.calculate_rental_cost(
        db, "user2", duration_hours=24, provider_cost=5.0, area_code="212"
    )
    assert result["area_code_fee"] == 0.50
    assert result["total_cost"] > result["base_cost"]


def test_pro_rental_area_code_included(db: Session, setup_tiers):
    """Pro users get rental area code selection included."""
    user = User(
        id="user3",
        email="user3@test.com",
        password_hash="test",
        subscription_tier="pro",
        credits=10.0,
    )
    db.add(user)
    db.commit()

    result = PricingCalculator.calculate_rental_cost(
        db, "user3", duration_hours=24, provider_cost=5.0, area_code="212"
    )
    assert result["area_code_fee"] == 0.0


def test_custom_rental_area_code_included(db: Session, setup_tiers):
    """Custom users get rental area code selection included."""
    user = User(
        id="user4",
        email="user4@test.com",
        password_hash="test",
        subscription_tier="custom",
        credits=10.0,
    )
    db.add(user)
    db.commit()

    result = PricingCalculator.calculate_rental_cost(
        db, "user4", duration_hours=24, provider_cost=5.0, area_code="212"
    )
    assert result["area_code_fee"] == 0.0


def test_rental_without_area_code_no_fee(db: Session, setup_tiers):
    """No area code fee when area code not requested for rentals."""
    user = User(
        id="user5",
        email="user5@test.com",
        password_hash="test",
        subscription_tier="payg",
        credits=10.0,
    )
    db.add(user)
    db.commit()

    result = PricingCalculator.calculate_rental_cost(
        db, "user5", duration_hours=24, provider_cost=5.0, area_code=None
    )
    assert result["area_code_fee"] == 0.0
