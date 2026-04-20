"""Unit tests for PricingCalculator.

v5.0: All tests pass provider_price — no fallback pricing.
"""

from unittest.mock import patch

import pytest

from app.services.pricing_calculator import PricingCalculator


class TestCalculateSmsCost:

    def test_basic_provider_price(self, db, regular_user):
        """provider_price × markup = base_cost."""
        regular_user.subscription_tier = "freemium"
        db.commit()
        with patch(
            "app.services.pricing_calculator.QuotaService.calculate_overage",
            return_value=0.0,
        ):
            res = PricingCalculator.calculate_sms_cost(
                db, regular_user.id, provider_price=1.50
            )
        # 1.50 × 1.1 = 1.65
        assert res["base_cost"] == 1.65
        assert res["provider_cost"] == 1.50
        assert res["markup"] == 1.1
        assert res["total_cost"] == 1.65

    def test_no_provider_price_raises(self, db, regular_user):
        """Must raise ValueError when provider_price is None."""
        regular_user.subscription_tier = "freemium"
        db.commit()
        with pytest.raises(ValueError, match="provider price unavailable"):
            PricingCalculator.calculate_sms_cost(db, regular_user.id)

    def test_zero_provider_price_raises(self, db, regular_user):
        """Must raise ValueError when provider_price is 0."""
        regular_user.subscription_tier = "payg"
        db.commit()
        with pytest.raises(ValueError, match="provider price unavailable"):
            PricingCalculator.calculate_sms_cost(
                db, regular_user.id, provider_price=0
            )

    def test_freemium_filters_raise(self, db, regular_user):
        """Freemium users cannot use filters."""
        regular_user.subscription_tier = "freemium"
        db.commit()
        with patch(
            "app.services.pricing_calculator.QuotaService.calculate_overage",
            return_value=0.0,
        ):
            with pytest.raises(ValueError, match="Filters not available"):
                PricingCalculator.calculate_sms_cost(
                    db,
                    regular_user.id,
                    filters={"area_code": "212"},
                    provider_price=1.50,
                )

    def test_overage_added(self, db, regular_user):
        """Overage charge is added to base cost."""
        regular_user.subscription_tier = "pro"
        db.commit()
        with patch(
            "app.services.pricing_calculator.QuotaService.calculate_overage",
            return_value=0.50,
        ):
            res = PricingCalculator.calculate_sms_cost(
                db, regular_user.id, provider_price=2.00
            )
        # 2.00 × 1.1 = 2.20 + 0.50 overage = 2.70
        assert res["base_cost"] == 2.20
        assert res["overage_charge"] == 0.50
        assert res["total_cost"] == 2.70


class TestCalculateRentalCost:

    def test_rental_with_provider_cost(self):
        """provider_cost × markup = total_cost."""
        res = PricingCalculator.calculate_rental_cost(
            None, "test", 24.0, provider_cost=5.00
        )
        assert res["total_cost"] == 5.50  # 5.00 × 1.1
        assert res["provider_cost"] == 5.00

    def test_rental_no_provider_cost_raises(self):
        """Must raise ValueError when provider_cost is None."""
        with pytest.raises(ValueError, match="provider cost unavailable"):
            PricingCalculator.calculate_rental_cost(None, "test", 24.0)


class TestValidateBalance:

    def test_freemium_uses_credits(self, db, regular_user):
        regular_user.subscription_tier = "freemium"
        regular_user.credits = 10.0
        db.commit()
        assert PricingCalculator.validate_balance(db, regular_user.id, 5.0) is True
        assert PricingCalculator.validate_balance(db, regular_user.id, 15.0) is False

    def test_payg_uses_credits(self, db, regular_user):
        regular_user.subscription_tier = "payg"
        regular_user.credits = 10.0
        db.commit()
        assert PricingCalculator.validate_balance(db, regular_user.id, 5.0) is True
        assert PricingCalculator.validate_balance(db, regular_user.id, 15.0) is False

    def test_pro_within_quota_zero_credits_allowed(self, db, regular_user):
        """Pro user within quota passes even with $0 credits."""
        regular_user.subscription_tier = "pro"
        regular_user.credits = 0.0
        db.commit()
        with patch(
            "app.services.pricing_calculator.QuotaService.calculate_overage",
            return_value=0.0,  # within quota
        ):
            result = PricingCalculator.validate_balance(
                db, regular_user.id, 1.65, tier="pro"
            )
        assert result is True

    def test_pro_over_quota_needs_credits(self, db, regular_user):
        """Pro user over quota needs credits >= overage (full cost)."""
        regular_user.subscription_tier = "pro"
        regular_user.credits = 1.00
        db.commit()
        with patch(
            "app.services.pricing_calculator.QuotaService.calculate_overage",
            return_value=1.65,  # over quota, full cost is overage
        ):
            result = PricingCalculator.validate_balance(
                db, regular_user.id, 1.65, tier="pro"
            )
        assert result is False  # credits(1.00) < overage(1.65)

    def test_pro_over_quota_sufficient_credits(self, db, regular_user):
        """Pro user over quota with enough credits passes."""
        regular_user.subscription_tier = "pro"
        regular_user.credits = 5.0
        db.commit()
        with patch(
            "app.services.pricing_calculator.QuotaService.calculate_overage",
            return_value=1.65,
        ):
            result = PricingCalculator.validate_balance(
                db, regular_user.id, 1.65, tier="pro"
            )
        assert result is True  # credits(5.0) >= overage(1.65)
