import pytest

from app.models.user import User
from app.services.pricing_calculator import PricingCalculator


class TestPricingCalculator:
    def test_calculate_sms_cost_freemium(self, db_session, regular_user):
        # Freemium: base 2.50, no filters allowed.
        # But with 0 quota, it adds 222% overage = 2.50 + 5.55 = 8.05
        res = PricingCalculator.calculate_sms_cost(db_session, regular_user.id)
        assert res["base_cost"] == 2.50
        assert res["total_cost"] == 8.05

        with pytest.raises(ValueError, match="Filters not available"):
            PricingCalculator.calculate_sms_cost(db_session, regular_user.id, filters={"isp": True})

    def test_calculate_sms_cost_payg(self, db_session, regular_user):
        regular_user.subscription_tier = "payg"
        db_session.commit()

        # PAYG: base 2.50, state/city +0.25, isp +0.50
        res = PricingCalculator.calculate_sms_cost(db_session, regular_user.id, filters={"state": True, "isp": True})
        assert res["base_cost"] == 2.50
        assert res["filter_charges"] == 0.75  # 0.25 + 0.50
        assert res["total_cost"] == 3.25

    def test_calculate_sms_cost_pro(self, db_session, regular_user):
        regular_user.subscription_tier = "pro"
        db_session.commit()

        # Pro: filters included
        res = PricingCalculator.calculate_sms_cost(db_session, regular_user.id, filters={"state": True, "isp": True})
        assert res["base_cost"] == 2.50
        assert res["filter_charges"] == 0.0
        assert res["total_cost"] == 2.50

    def test_validate_balance(self, db_session, regular_user):
        # Freemium check: uses bonus_sms_balance
        regular_user.bonus_sms_balance = 2.0
        assert PricingCalculator.validate_balance(db_session, regular_user.id, 5.0) is True

        regular_user.bonus_sms_balance = 0.0
        assert PricingCalculator.validate_balance(db_session, regular_user.id, 5.0) is False

        # Paid tier check: uses credits
        regular_user.subscription_tier = "payg"
        regular_user.credits = 10.0
        assert PricingCalculator.validate_balance(db_session, regular_user.id, 5.0) is True
        assert PricingCalculator.validate_balance(db_session, regular_user.id, 15.0) is False

    def test_get_pricing_breakdown(self, db_session, regular_user):
        regular_user.subscription_tier = "pro"
        db_session.commit()

        res = PricingCalculator.get_pricing_breakdown(db_session, regular_user.id)
        assert res["tier"] == "pro"
        assert "quota_limit" in res
        assert "user_balance" in res
