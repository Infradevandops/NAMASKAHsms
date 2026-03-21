"""Unit tests for VerificationPricingService."""

from unittest.mock import patch

import pytest

from app.services.verification_pricing_service import VerificationPricingService


class TestDeductCost:

    def test_payg_full_cost_deducted(self, db, regular_user):
        regular_user.subscription_tier = "payg"
        regular_user.credits = 10.0
        db.commit()
        with patch("app.services.verification_pricing_service.QuotaService.calculate_overage", return_value=0.0), \
             patch("app.services.verification_pricing_service.QuotaService.add_quota_usage"):
            VerificationPricingService.deduct_cost(db, regular_user.id, 2.50, tier="payg")
        db.refresh(regular_user)
        assert float(regular_user.credits) == pytest.approx(7.50)

    def test_pro_within_quota_credits_not_deducted(self, db, regular_user):
        regular_user.subscription_tier = "pro"
        regular_user.credits = 5.0
        db.commit()
        with patch("app.services.verification_pricing_service.QuotaService.calculate_overage", return_value=0.0), \
             patch("app.services.verification_pricing_service.QuotaService.add_quota_usage"):
            VerificationPricingService.deduct_cost(db, regular_user.id, 0.30, tier="pro")
        db.refresh(regular_user)
        # No overage — credits unchanged
        assert float(regular_user.credits) == pytest.approx(5.0)

    def test_pro_overage_only_overage_deducted(self, db, regular_user):
        regular_user.subscription_tier = "pro"
        regular_user.credits = 5.0
        db.commit()
        with patch("app.services.verification_pricing_service.QuotaService.calculate_overage", return_value=0.50), \
             patch("app.services.verification_pricing_service.QuotaService.add_quota_usage"):
            VerificationPricingService.deduct_cost(db, regular_user.id, 0.80, tier="pro")
        db.refresh(regular_user)
        assert float(regular_user.credits) == pytest.approx(4.50)

    def test_custom_within_quota_credits_not_deducted(self, db, regular_user):
        regular_user.subscription_tier = "custom"
        regular_user.credits = 3.0
        db.commit()
        with patch("app.services.verification_pricing_service.QuotaService.calculate_overage", return_value=0.0), \
             patch("app.services.verification_pricing_service.QuotaService.add_quota_usage"):
            VerificationPricingService.deduct_cost(db, regular_user.id, 0.20, tier="custom")
        db.refresh(regular_user)
        assert float(regular_user.credits) == pytest.approx(3.0)

    def test_freemium_deducts_bonus_balance(self, db, regular_user):
        regular_user.subscription_tier = "freemium"
        regular_user.bonus_sms_balance = 3
        db.commit()
        with patch("app.services.verification_pricing_service.QuotaService.add_quota_usage"):
            VerificationPricingService.deduct_cost(db, regular_user.id, 2.22, tier="freemium")
        db.refresh(regular_user)
        assert regular_user.bonus_sms_balance == 2
