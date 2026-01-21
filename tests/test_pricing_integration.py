"""Integration tests for pricing enforcement."""

import uuid

import pytest
from sqlalchemy.orm import Session

from app.models.user import User
from app.services.api_key_service import APIKeyService
from app.services.pricing_calculator import PricingCalculator
from app.services.quota_service import QuotaService
from app.services.transaction_service import TransactionService
from app.services.verification_pricing_service import VerificationPricingService


@pytest.fixture
def db(db_session):
    """Get database session from conftest."""
    return db_session


@pytest.fixture
def users(db: Session):
    """Create test users for all tiers."""
    users = {}
    tiers = ["freemium", "payg", "pro", "custom"]

    for tier in tiers:
        user = User(
            id=str(uuid.uuid4()),
            email=f"{tier}_{uuid.uuid4()}@test.com",
            password_hash="hash",
            subscription_tier=tier,
            bonus_sms_balance=9.0 if tier == "freemium" else 0.0,
            credits=100.0 if tier != "freemium" else 0.0,
        )
        db.add(user)
        users[tier] = user

    db.commit()
    return users


class TestPricingEnforcementFlow:
    """Test complete pricing enforcement flow."""

    def test_freemium_purchase_flow(self, db: Session, users: dict):
        """Test freemium user purchase flow."""
        user = users["freemium"]

        # Calculate cost
        cost_info = PricingCalculator.calculate_sms_cost(db, user.id)
        assert cost_info["tier"] == "freemium"

        # Validate balance
        assert PricingCalculator.validate_balance(db, user.id, cost_info["total_cost"])

        # Deduct cost
        VerificationPricingService.deduct_cost(db, user.id, cost_info["total_cost"])

        # Verify deduction
        user = db.query(User).filter(User.id == user.id).first()
        assert user.bonus_sms_balance == 8.0

    def test_payg_with_filters_flow(self, db: Session, users: dict):
        """Test PAYG user with filters."""
        user = users["payg"]
        filters = {"state": True, "isp": True}

        # Calculate cost with filters
        cost_info = PricingCalculator.calculate_sms_cost(db, user.id, filters)
        assert cost_info["filter_charges"] == 0.75
        assert cost_info["total_cost"] == 3.25

        # Validate balance
        assert PricingCalculator.validate_balance(db, user.id, cost_info["total_cost"])

        # Log transaction
        tx_id = TransactionService.log_sms_purchase(
            db, user.id, cost_info["total_cost"], "payg", "telegram", filters
        )
        assert tx_id is not None

    def test_pro_quota_tracking_flow(self, db: Session, users: dict):
        """Test Pro user quota tracking."""
        user = users["pro"]

        # Get initial quota
        quota_info = QuotaService.get_monthly_usage(db, user.id)
        assert quota_info["quota_limit"] == 15.0
        assert quota_info["quota_used"] == 0.0

        # Add usage
        QuotaService.add_quota_usage(db, user.id, 10.0)

        # Verify usage
        quota_info = QuotaService.get_monthly_usage(db, user.id)
        assert quota_info["quota_used"] == 10.0
        assert quota_info["remaining"] == 5.0

    def test_pro_overage_calculation_flow(self, db: Session, users: dict):
        """Test Pro user overage calculation."""
        user = users["pro"]

        # Add usage near limit
        QuotaService.add_quota_usage(db, user.id, 14.0)

        # Calculate overage for next SMS
        overage = QuotaService.calculate_overage(db, user.id, 2.50)
        assert overage == pytest.approx(0.45, rel=1e-2)  # (14 + 2.50 - 15) * 0.30

    def test_custom_api_key_limit_flow(self, db: Session, users: dict):
        """Test Custom user API key creation."""
        user = users["custom"]

        # Can create keys
        assert APIKeyService.can_create_key(db, user.id)

        # Get remaining
        remaining = APIKeyService.get_remaining_keys(db, user.id)
        assert remaining == 999  # Unlimited

        # Create key
        key_info = APIKeyService.create_key(db, user.id, "Test Key")
        assert key_info["name"] == "Test Key"

    def test_freemium_cannot_use_filters_flow(self, db: Session, users: dict):
        """Test freemium cannot use filters."""
        user = users["freemium"]
        filters = {"state": True}

        # Should raise error
        with pytest.raises(ValueError, match="Filters not available"):
            PricingCalculator.calculate_sms_cost(db, user.id, filters)

    def test_complete_transaction_flow(self, db: Session, users: dict):
        """Test complete transaction from purchase to logging."""
        user = users["pro"]

        # 1. Calculate cost
        cost_info = VerificationPricingService.validate_and_calculate_cost(db, user.id)

        # 2. Deduct cost
        VerificationPricingService.deduct_cost(db, user.id, cost_info["total_cost"])

        # 3. Log transaction
        tx_id = TransactionService.log_sms_purchase(
            db, user.id, cost_info["total_cost"], "pro", "telegram"
        )

        # 4. Verify all changes
        user = db.query(User).filter(User.id == user.id).first()
        assert user.credits < 100.0
        assert tx_id is not None
