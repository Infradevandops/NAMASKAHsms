"""Unit tests for PricingCalculator."""
import pytest
from app.services.pricing_calculator import PricingCalculator
from app.models.user import User

class TestPricingLogic:
    """Test pricing calculator logic."""

    def test_get_filter_charges_payg(self, db_session):
        """Test filter charges for PAYG user."""
        user = User(email="payg_filter@example.com", subscription_tier="payg", credits=10.0)
        db_session.add(user)
        db_session.commit()

        # State filter only
        charges = PricingCalculator.get_filter_charges(db_session, user.id, {"state": "CA"})
        assert charges == 0.25

        # ISP filter only
        charges = PricingCalculator.get_filter_charges(db_session, user.id, {"isp": "Comcast"})
        assert charges == 0.50

        # Both
        charges = PricingCalculator.get_filter_charges(db_session, user.id, {"state": "CA", "isp": "Comcast"})
        assert charges == 0.75
        
        # None
        charges = PricingCalculator.get_filter_charges(db_session, user.id, {})
        assert charges == 0.0

    def test_get_filter_charges_pro(self, db_session):
        """Test filter charges for Pro user (free filters)."""
        user = User(email="pro_filter@example.com", subscription_tier="pro", credits=10.0)
        db_session.add(user)
        db_session.commit()

        charges = PricingCalculator.get_filter_charges(db_session, user.id, {"state": "CA", "isp": "Comcast"})
        assert charges == 0.0

    def test_get_filter_charges_freemium_error(self, db_session):
        """Test filter charges raises error for Freemium user."""
        user = User(email="free_filter@example.com", subscription_tier="freemium", credits=0.0)
        db_session.add(user)
        db_session.commit()

        with pytest.raises(ValueError, match="Filters not available"):
            PricingCalculator.get_filter_charges(db_session, user.id, {"state": "CA"})

    def test_get_pricing_breakdown(self, db_session):
        """Test full pricing breakdown."""
        user = User(email="breakdown@example.com", subscription_tier="payg", credits=100.0)
        db_session.add(user)
        db_session.commit()

        # Mock QuotaService?? No need if it uses defaults (quota=0 for PAYG)
        # Assuming QuotaService calls work with defaults.

        breakdown = PricingCalculator.get_pricing_breakdown(db_session, user.id, {"state": "NY"})
        
        assert breakdown["tier"] == "payg"
        assert breakdown["base_cost"] == 2.50
        assert breakdown["filter_charges"] == 0.25
        # Overage calculation in QuotaService might need attention if QuotaService.get_monthly_usage returns 0
        # If overage_rate is 0 for PAYG (as we patched), overage_charge should be 0.
        assert breakdown["overage_charge"] == 0.0 
        assert breakdown["total_cost"] == 2.75
        assert breakdown["user_balance"] == 100.0
        assert breakdown["sufficient_balance"] is True
