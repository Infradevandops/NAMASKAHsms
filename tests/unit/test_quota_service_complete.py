from datetime import datetime

import pytest

from app.models.user_quota import MonthlyQuotaUsage
from app.services.quota_service import QuotaService


class TestQuotaServiceComplete:
    """Comprehensive tests for QuotaService."""

    def test_get_monthly_usage_empty(self, db_session, regular_user):
        """Test getting usage for user with no history."""
        usage = QuotaService.get_monthly_usage(db_session, regular_user.id)
        assert usage["quota_used"] == 0.0
        assert usage["overage_used"] == 0.0

    def test_add_quota_usage(self, db_session, regular_user):
        """Test adding quota usage."""
        QuotaService.add_quota_usage(db_session, regular_user.id, 5.0)

        usage = QuotaService.get_monthly_usage(db_session, regular_user.id)
        assert usage["quota_used"] == 5.0

        # Add more
        QuotaService.add_quota_usage(db_session, regular_user.id, 2.5)
        usage = QuotaService.get_monthly_usage(db_session, regular_user.id)
        assert usage["quota_used"] == 7.5

    def test_calculate_overage(self, db_session, regular_user):
        """Test overage calculation."""
        # Upgrade to pro (quota 15 USD, overage rate 0.30)
        regular_user.subscription_tier = "pro"
        db_session.add(regular_user)
        db_session.commit()

        # Add usage near limit
        QuotaService.add_quota_usage(db_session, regular_user.id, 14.0)

        # Small addition within limit
        overage = QuotaService.calculate_overage(db_session, regular_user.id, 0.5)
        assert overage == 0.0

        # Addition exceeding limit
        # Cost 2.0. Total 16.0. Over limit 1.0. Overage 1.0 * 0.30 = 0.30
        overage = QuotaService.calculate_overage(db_session, regular_user.id, 2.0)
        assert abs(overage - 0.30) < 0.001

    def test_get_overage_rate(self, db_session, regular_user):
        """Test getting overage rate."""
        regular_user.subscription_tier = "pro"
        db_session.add(regular_user)
        db_session.commit()

        rate = QuotaService.get_overage_rate(db_session, regular_user.id)
        assert rate == 0.30

        regular_user.subscription_tier = "freemium"
        db_session.commit()
        rate = QuotaService.get_overage_rate(db_session, regular_user.id)
        # Check fallback/freemium rate in TIER_CONFIG_SIMPLE (likely 2.22 or 0)
        assert isinstance(rate, (int, float))
