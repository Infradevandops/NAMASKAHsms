"""Unit tests for PricingCalculator — v5.0 clean pricing model."""

import pytest

from app.models.user import User
from app.services.pricing_calculator import PricingCalculator


class TestPricingLogic:
    """Test pricing calculator logic."""

    def test_calculate_sms_cost_payg(self, db_session):
        """PAYG: cost = provider_price * markup, no overage."""
        user = User(
            email="payg_filter@example.com", subscription_tier="payg", credits=10.0
        )
        db_session.add(user)
        db_session.commit()

        result = PricingCalculator.calculate_sms_cost(
            db_session, user.id, {}, provider_price=2.00
        )
        assert result["provider_cost"] == 2.00
        assert result["base_cost"] > 0
        assert result["overage_charge"] == 0.0

    def test_calculate_sms_cost_pro(self, db_session):
        """Pro: within quota, overage = 0."""
        user = User(
            email="pro_filter@example.com", subscription_tier="pro", credits=10.0
        )
        db_session.add(user)
        db_session.commit()

        result = PricingCalculator.calculate_sms_cost(
            db_session, user.id, {}, provider_price=2.00
        )
        assert result["overage_charge"] == 0.0
        assert result["tier"] == "pro"

    def test_calculate_sms_cost_freemium_no_filters(self, db_session):
        """Freemium: no filters allowed."""
        user = User(
            email="free_filter@example.com", subscription_tier="freemium", credits=0.0
        )
        db_session.add(user)
        db_session.commit()

        with pytest.raises(ValueError, match="Filters not available"):
            PricingCalculator.calculate_sms_cost(
                db_session, user.id, {"state": "CA"}, provider_price=2.00
            )

    def test_get_pricing_breakdown(self, db_session):
        """Breakdown includes all expected keys."""
        user = User(
            email="breakdown@example.com", subscription_tier="payg", credits=100.0
        )
        db_session.add(user)
        db_session.commit()

        breakdown = PricingCalculator.get_pricing_breakdown(
            db_session, user.id, {}, provider_price=2.00
        )

        assert breakdown["tier"] == "payg"
        assert breakdown["base_cost"] > 0
        assert breakdown["overage_charge"] == 0.0
        assert breakdown["total_cost"] > 0
        assert breakdown["user_balance"] == 100.0
        assert breakdown["sufficient_balance"] is True
        assert "provider_cost" in breakdown
        assert "markup" in breakdown
