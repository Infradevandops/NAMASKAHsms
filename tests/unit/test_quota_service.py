"""Unit tests for QuotaService."""

from unittest.mock import patch

import pytest

from app.services.quota_service import QuotaService


class TestGetMonthlyUsage:

    def test_empty_usage_returns_zeros(self, db, regular_user):
        with patch("app.services.quota_service.TierConfig.get_tier_config") as mock_cfg:
            mock_cfg.return_value = {"quota_usd": 0.0}
            usage = QuotaService.get_monthly_usage(db, regular_user.id)
        assert usage["quota_used"] == 0.0
        assert usage["quota_limit"] == 0.0

    def test_uses_passed_tier_not_user_field(self, db, regular_user):
        """Caller-supplied tier must override user.subscription_tier."""
        regular_user.subscription_tier = "freemium"
        db.commit()
        with patch("app.services.quota_service.TierConfig.get_tier_config") as mock_cfg:
            mock_cfg.return_value = {"quota_usd": 15.0}
            usage = QuotaService.get_monthly_usage(db, regular_user.id, tier="pro")
            mock_cfg.assert_called_with("pro", db)
        assert usage["quota_limit"] == 15.0

    def test_expired_pro_user_gets_freemium_quota_limits(self, db, regular_user):
        """When caller resolves expired tier to freemium, quota limit should be 0."""
        regular_user.subscription_tier = "pro"  # stale DB value
        db.commit()
        with patch("app.services.quota_service.TierConfig.get_tier_config") as mock_cfg:
            mock_cfg.return_value = {"quota_usd": 0.0}
            # Caller passes resolved tier=freemium (from TierManager)
            usage = QuotaService.get_monthly_usage(db, regular_user.id, tier="freemium")
            mock_cfg.assert_called_with("freemium", db)
        assert usage["quota_limit"] == 0.0


class TestAddQuotaUsage:

    def test_add_quota_usage(self, db, regular_user):
        with patch("app.services.quota_service.TierConfig.get_tier_config") as mock_cfg:
            mock_cfg.return_value = {"quota_usd": 15.0}
            QuotaService.add_quota_usage(db, regular_user.id, 10.0)
            usage = QuotaService.get_monthly_usage(db, regular_user.id)
        assert usage["quota_used"] == 10.0


class TestCalculateOverage:

    def test_no_overage_within_quota(self, db, regular_user):
        regular_user.subscription_tier = "pro"
        db.commit()
        with patch("app.services.quota_service.TierConfig.get_tier_config") as mock_cfg:
            mock_cfg.return_value = {"quota_usd": 15.0, "overage_rate": 0.30}
            overage = QuotaService.calculate_overage(
                db, regular_user.id, 5.0, tier="pro"
            )
        assert overage == 0.0

    def test_overage_calculated_correctly(self, db, regular_user):
        regular_user.subscription_tier = "pro"
        db.commit()
        with patch("app.services.quota_service.TierConfig.get_tier_config") as mock_cfg:
            mock_cfg.return_value = {"quota_usd": 15.0, "overage_rate": 0.30}
            # Get current usage baseline
            baseline = QuotaService.get_monthly_usage(db, regular_user.id, tier="pro")
            baseline_used = baseline["quota_used"]
            # Add 10 usage
            QuotaService.add_quota_usage(db, regular_user.id, 10.0)
            # Adding 10 more: if total > 15, overage = (used+10) - 15 * 0.30
            overage = QuotaService.calculate_overage(
                db, regular_user.id, 10.0, tier="pro"
            )
            expected_overage_amount = max(0, (baseline_used + 10.0 + 10.0) - 15.0)
            assert overage == pytest.approx(expected_overage_amount * 0.30)

    def test_get_overage_rate_pro(self, db, regular_user):
        regular_user.subscription_tier = "pro"
        db.commit()
        with patch("app.services.quota_service.TierConfig.get_tier_config") as mock_cfg:
            mock_cfg.return_value = {"overage_rate": 0.30}
            rate = QuotaService.get_overage_rate(db, regular_user.id)
        assert rate == 0.30
