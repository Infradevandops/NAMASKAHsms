"""Unit tests for PricingCalculator."""

from unittest.mock import patch

import pytest

from app.services.pricing_calculator import PricingCalculator


class TestCalculateSmsCost:

    def test_freemium_no_filters(self, db, regular_user):
        regular_user.subscription_tier = "freemium"
        db.commit()
        with patch(
            "app.services.pricing_calculator.TierConfig.get_tier_config"
        ) as mock_cfg, patch(
            "app.services.pricing_calculator.QuotaService.calculate_overage",
            return_value=0.0,
        ):
            mock_cfg.return_value = {"base_sms_cost": 2.22}
            res = PricingCalculator.calculate_sms_cost(db, regular_user.id)
        assert res["base_cost"] == 2.22
        assert res["filter_charges"] == 0.0

    def test_freemium_filters_raise(self, db, regular_user):
        regular_user.subscription_tier = "freemium"
        db.commit()
        with patch(
            "app.services.pricing_calculator.TierConfig.get_tier_config"
        ) as mock_cfg, patch(
            "app.services.pricing_calculator.QuotaService.calculate_overage",
            return_value=0.0,
        ):
            mock_cfg.return_value = {"base_sms_cost": 2.22}
            with pytest.raises(ValueError, match="Filters not available"):
                PricingCalculator.calculate_sms_cost(
                    db, regular_user.id, filters={"area_code": "212"}
                )

    def test_payg_area_code_premium(self, db, regular_user):
        regular_user.subscription_tier = "payg"
        db.commit()
        with patch(
            "app.services.pricing_calculator.TierConfig.get_tier_config"
        ) as mock_cfg, patch(
            "app.services.pricing_calculator.QuotaService.calculate_overage",
            return_value=0.0,
        ):
            mock_cfg.return_value = {"base_sms_cost": 2.50}
            res = PricingCalculator.calculate_sms_cost(
                db, regular_user.id, filters={"area_code": "212"}
            )
        assert res["base_cost"] == 2.50
        assert res["area_code_surcharge"] == 0.50
        assert res["total_cost"] == 3.00

    def test_payg_carrier_premium(self, db, regular_user):
        regular_user.subscription_tier = "payg"
        db.commit()
        with patch(
            "app.services.pricing_calculator.TierConfig.get_tier_config"
        ) as mock_cfg, patch(
            "app.services.pricing_calculator.QuotaService.calculate_overage",
            return_value=0.0,
        ):
            mock_cfg.return_value = {"base_sms_cost": 2.50}
            res = PricingCalculator.calculate_sms_cost(
                db, regular_user.id, filters={"carrier": "verizon"}
            )
        assert res["carrier_surcharge"] == 0.30
        assert res["total_cost"] == 2.80

    def test_pro_filters_free(self, db, regular_user):
        regular_user.subscription_tier = "pro"
        db.commit()
        with patch(
            "app.services.pricing_calculator.TierConfig.get_tier_config"
        ) as mock_cfg, patch(
            "app.services.pricing_calculator.QuotaService.calculate_overage",
            return_value=0.0,
        ):
            mock_cfg.return_value = {"base_sms_cost": 0.30}
            res = PricingCalculator.calculate_sms_cost(
                db, regular_user.id, filters={"area_code": "212", "carrier": "verizon"}
            )
        assert res["filter_charges"] == 0.0
        assert res["total_cost"] == 0.30


class TestValidateBalance:

    def test_freemium_uses_bonus_balance(self, db, regular_user):
        regular_user.subscription_tier = "freemium"
        regular_user.bonus_sms_balance = 2.0
        db.commit()
        assert PricingCalculator.validate_balance(db, regular_user.id, 5.0) is True

    def test_freemium_no_bonus_blocked(self, db, regular_user):
        regular_user.subscription_tier = "freemium"
        regular_user.bonus_sms_balance = 0.0
        db.commit()
        assert PricingCalculator.validate_balance(db, regular_user.id, 5.0) is False

    def test_payg_uses_credits(self, db, regular_user):
        regular_user.subscription_tier = "payg"
        regular_user.credits = 10.0
        db.commit()
        assert PricingCalculator.validate_balance(db, regular_user.id, 5.0) is True
        assert PricingCalculator.validate_balance(db, regular_user.id, 15.0) is False

    def test_pro_within_quota_zero_credits_allowed(self, db, regular_user):
        regular_user.subscription_tier = "pro"
        regular_user.credits = 0.0
        db.commit()
        with patch(
            "app.services.pricing_calculator.QuotaService.get_monthly_usage"
        ) as mock_usage, patch(
            "app.services.pricing_calculator.TierConfig.get_tier_config"
        ) as mock_cfg:
            mock_usage.return_value = {
                "remaining": 10.0,
                "quota_limit": 15.0,
                "quota_used": 5.0,
            }
            mock_cfg.return_value = {"base_sms_cost": 0.30}
            result = PricingCalculator.validate_balance(
                db, regular_user.id, 0.30, tier="pro"
            )
        assert result is True

    def test_pro_quota_exhausted_zero_credits_blocked(self, db, regular_user):
        regular_user.subscription_tier = "pro"
        regular_user.credits = 0.0
        db.commit()
        with patch(
            "app.services.pricing_calculator.QuotaService.get_monthly_usage"
        ) as mock_usage, patch(
            "app.services.pricing_calculator.QuotaService.calculate_overage"
        ) as mock_overage, patch(
            "app.services.pricing_calculator.TierConfig.get_tier_config"
        ) as mock_cfg:
            mock_usage.return_value = {
                "remaining": 0.0,
                "quota_limit": 15.0,
                "quota_used": 15.0,
            }
            mock_overage.return_value = 0.30
            mock_cfg.return_value = {"base_sms_cost": 0.30}
            result = PricingCalculator.validate_balance(
                db, regular_user.id, 0.30, tier="pro"
            )
        assert result is False

    def test_pro_partial_quota_overage_requires_credits(self, db, regular_user):
        regular_user.subscription_tier = "pro"
        regular_user.credits = 1.0
        db.commit()
        with patch(
            "app.services.pricing_calculator.QuotaService.get_monthly_usage"
        ) as mock_usage, patch(
            "app.services.pricing_calculator.QuotaService.calculate_overage"
        ) as mock_overage, patch(
            "app.services.pricing_calculator.TierConfig.get_tier_config"
        ) as mock_cfg:
            mock_usage.return_value = {
                "remaining": 0.0,
                "quota_limit": 15.0,
                "quota_used": 15.0,
            }
            mock_overage.return_value = 0.50
            mock_cfg.return_value = {"base_sms_cost": 0.30}
            result = PricingCalculator.validate_balance(
                db, regular_user.id, 0.50, tier="pro"
            )
        assert result is True  # credits(1.0) >= overage(0.50)
