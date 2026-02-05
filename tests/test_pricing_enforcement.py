"""Tests for pricing enforcement."""


import uuid
import pytest
from sqlalchemy.orm import Session
from app.models.user import User
from app.services.pricing_calculator import PricingCalculator
from app.services.quota_service import QuotaService

@pytest.fixture
def freemium_user(db: Session):

    """Create freemium test user."""
    user = User(
        id=str(uuid.uuid4()),
        email=f"freemium_{uuid.uuid4()}@test.com",
        password_hash="hash",
        subscription_tier="freemium",
        bonus_sms_balance=9.0,
        credits=0.0,
    )
    db.add(user)
    db.commit()
    return user


@pytest.fixture
def payg_user(db: Session):

    """Create pay-as-you-go test user."""
    user = User(
        id=str(uuid.uuid4()),
        email=f"payg_{uuid.uuid4()}@test.com",
        password_hash="hash",
        subscription_tier="payg",
        credits=50.0,
    )
    db.add(user)
    db.commit()
    return user


@pytest.fixture
def pro_user(db: Session):

    """Create pro tier test user."""
    user = User(
        id=str(uuid.uuid4()),
        email=f"pro_{uuid.uuid4()}@test.com",
        password_hash="hash",
        subscription_tier="pro",
        credits=100.0,
    )
    db.add(user)
    db.commit()
    return user


class TestQuotaService:

    """Test quota tracking."""

    def test_get_monthly_usage_new_month(self, db: Session, pro_user: User):

        """Test getting usage for new month."""
        usage = QuotaService.get_monthly_usage(db, pro_user.id)
        assert usage["quota_used"] == 0.0
        assert usage["overage_used"] == 0.0
        assert usage["quota_limit"] == 15.0  # Pro tier from config
        assert usage["remaining"] == 15.0

    def test_add_quota_usage(self, db: Session, pro_user: User):

        """Test adding quota usage."""
        QuotaService.add_quota_usage(db, pro_user.id, 5.0)
        usage = QuotaService.get_monthly_usage(db, pro_user.id)
        assert usage["quota_used"] == 5.0
        assert usage["remaining"] == 10.0

    def test_calculate_overage_within_quota(self, db: Session, pro_user: User):

        """Test overage calculation within quota."""
        overage = QuotaService.calculate_overage(db, pro_user.id, 10.0)
        assert overage == 0.0

    def test_calculate_overage_exceeds_quota(self, db: Session, pro_user: User):

        """Test overage calculation exceeding quota."""
        QuotaService.add_quota_usage(db, pro_user.id, 25.0)
        # Quota for pro is 15. Already at 25.
        # Adding 10. Total 35.
        # Excess is 35 - 15 = 20.
        # Rate is 0.30. Overage = 20 * 0.30 = 6.0
        overage = QuotaService.calculate_overage(db, pro_user.id, 10.0)
        assert abs(overage - 6.0) < 0.01

    def test_get_overage_rate(self, db: Session, pro_user: User):

        """Test getting overage rate."""
        rate = QuotaService.get_overage_rate(db, pro_user.id)
        assert rate == 0.30  # Pro tier


class TestPricingCalculator:

        """Test pricing calculations."""

    def test_freemium_no_filters(self, db: Session, freemium_user: User):

        """Test freemium pricing without filters."""
        # Freemium quota is 0. Base cost is 2.50.
        # Overage = (0 + 2.50) * 2.22 = 5.55
        cost = PricingCalculator.calculate_sms_cost(db, freemium_user.id, {})
        assert cost["base_cost"] == 2.50
        assert abs(cost["overage_charge"] - 5.55) < 0.01
        assert abs(cost["total_cost"] - 8.05) < 0.01

    def test_freemium_filters_blocked(self, db: Session, freemium_user: User):

        """Test freemium cannot use filters."""
        with pytest.raises(ValueError, match="Filters not available"):
            PricingCalculator.calculate_sms_cost(db, freemium_user.id, {"state": True})

    def test_payg_with_state_filter(self, db: Session, payg_user: User):

        """Test PAYG pricing with state filter."""
        cost = PricingCalculator.calculate_sms_cost(db, payg_user.id, {"state": True})
        assert cost["base_cost"] == 2.50
        assert cost["filter_charges"] == 0.25
        # PAYG quota is 0. Overage rate is 0.
        assert cost["overage_charge"] == 0.0
        assert cost["total_cost"] == 2.75

    def test_pro_filters_included(self, db: Session, pro_user: User):

        """Test Pro tier includes filters."""
        cost = PricingCalculator.calculate_sms_cost(db, pro_user.id, {"state": True, "isp": True})
        assert cost["filter_charges"] == 0.0  # Included in Pro

    def test_validate_balance_freemium_sufficient(self, db: Session, freemium_user: User):

        """Test balance validation for freemium with bonus SMS."""
        assert PricingCalculator.validate_balance(db, freemium_user.id, 2.50) is True

    def test_validate_balance_payg_sufficient(self, db: Session, payg_user: User):

        """Test balance validation for PAYG with credits."""
        assert PricingCalculator.validate_balance(db, payg_user.id, 10.0) is True

    def test_get_pricing_breakdown(self, db: Session, pro_user: User):

        """Test pricing breakdown."""
        breakdown = PricingCalculator.get_pricing_breakdown(db, pro_user.id, {"state": True})
        assert breakdown["tier"] == "pro"
        assert breakdown["quota_limit"] == 15.0
        assert breakdown["user_balance"] == 100.0
        assert breakdown["sufficient_balance"] is True
