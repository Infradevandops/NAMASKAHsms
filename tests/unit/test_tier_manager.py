"""Unit tests for TierManager service."""

from datetime import datetime, timedelta, timezone
from unittest.mock import Mock, patch

import pytest

from app.models.api_key import APIKey
from app.models.user import User
from app.services.tier_manager import TierManager


@pytest.fixture
def mock_db():
    return Mock()


@pytest.fixture
def tier_manager(mock_db):
    return TierManager(mock_db)


@pytest.fixture
def mock_user():
    user = Mock(spec=User)
    user.id = "user123"
    user.subscription_tier = "freemium"
    user.tier_expires_at = None
    user.is_admin = False
    return user


class TestGetUserTier:
    def test_returns_freemium_for_nonexistent_user(self, tier_manager, mock_db):
        mock_db.query().filter().first.return_value = None
        assert tier_manager.get_user_tier("nonexistent") == "freemium"

    def test_returns_user_tier(self, tier_manager, mock_db, mock_user):
        mock_user.subscription_tier = "pro"
        mock_db.query().filter().first.return_value = mock_user
        assert tier_manager.get_user_tier("user123") == "pro"

    def test_defaults_to_freemium_for_none_tier(self, tier_manager, mock_db, mock_user):
        mock_user.subscription_tier = None
        mock_db.query().filter().first.return_value = mock_user
        assert tier_manager.get_user_tier("user123") == "freemium"

    def test_defaults_unknown_tier_to_freemium(self, tier_manager, mock_db, mock_user):
        mock_user.subscription_tier = "unknown_tier"
        mock_db.query().filter().first.return_value = mock_user
        assert tier_manager.get_user_tier("user123") == "freemium"

    def test_admin_keeps_tier_regardless_of_expiry(
        self, tier_manager, mock_db, mock_user
    ):
        mock_user.is_admin = True
        mock_user.subscription_tier = "custom"
        mock_user.tier_expires_at = datetime.now(timezone.utc) - timedelta(days=30)
        mock_db.query().filter().first.return_value = mock_user
        assert tier_manager.get_user_tier("user123") == "custom"

    def test_expired_tier_downgrades_to_freemium(
        self, tier_manager, mock_db, mock_user
    ):
        mock_user.subscription_tier = "pro"
        mock_user.tier_expires_at = datetime.now(timezone.utc) - timedelta(days=1)
        mock_db.query().filter().first.return_value = mock_user
        result = tier_manager.get_user_tier("user123")
        assert result == "freemium"
        assert mock_user.subscription_tier == "freemium"
        assert mock_user.tier_expires_at is None
        mock_db.commit.assert_called_once()

    def test_non_expired_tier_remains(self, tier_manager, mock_db, mock_user):
        mock_user.subscription_tier = "pro"
        mock_user.tier_expires_at = datetime.now(timezone.utc) + timedelta(days=30)
        mock_db.query().filter().first.return_value = mock_user
        assert tier_manager.get_user_tier("user123") == "pro"

    def test_handles_naive_datetime_expiry(self, tier_manager, mock_db, mock_user):
        mock_user.subscription_tier = "pro"
        mock_user.tier_expires_at = datetime.now() - timedelta(days=1)
        mock_db.query().filter().first.return_value = mock_user
        result = tier_manager.get_user_tier("user123")
        assert result == "freemium"


class TestCheckFeatureAccess:
    @patch("app.services.tier_manager.TierConfig.get_tier_config")
    def test_api_access_for_pro_tier(
        self, mock_config, tier_manager, mock_db, mock_user
    ):
        mock_user.subscription_tier = "pro"
        mock_db.query().filter().first.return_value = mock_user
        mock_config.return_value = {"has_api_access": True}
        assert tier_manager.check_feature_access("user123", "api_access") is True

    @patch("app.services.tier_manager.TierConfig.get_tier_config")
    def test_api_access_denied_for_freemium(
        self, mock_config, tier_manager, mock_db, mock_user
    ):
        mock_db.query().filter().first.return_value = mock_user
        mock_config.return_value = {"has_api_access": False}
        assert tier_manager.check_feature_access("user123", "api_access") is False

    @patch("app.services.tier_manager.TierConfig.get_tier_config")
    def test_area_code_selection_access(
        self, mock_config, tier_manager, mock_db, mock_user
    ):
        mock_user.subscription_tier = "payg"
        mock_db.query().filter().first.return_value = mock_user
        mock_config.return_value = {"has_area_code_selection": True}
        assert (
            tier_manager.check_feature_access("user123", "area_code_selection") is True
        )

    @patch("app.services.tier_manager.TierConfig.get_tier_config")
    def test_unknown_feature_returns_false(
        self, mock_config, tier_manager, mock_db, mock_user
    ):
        mock_db.query().filter().first.return_value = mock_user
        mock_config.return_value = {}
        assert tier_manager.check_feature_access("user123", "unknown_feature") is False


class TestGetTierLimits:
    @patch("app.services.tier_manager.TierConfig.get_tier_config")
    def test_returns_tier_limits(self, mock_config, tier_manager, mock_db, mock_user):
        mock_db.query().filter().first.return_value = mock_user
        mock_config.return_value = {
            "daily_verification_limit": 50,
            "monthly_verification_limit": 1000,
            "api_key_limit": 5,
            "rate_limit_per_minute": 20,
            "rate_limit_per_hour": 500,
        }
        limits = tier_manager.get_tier_limits("user123")
        assert limits["daily_verification_limit"] == 50
        assert limits["monthly_verification_limit"] == 1000
        assert limits["api_key_limit"] == 5

    @patch("app.services.tier_manager.TierConfig.get_tier_config")
    def test_uses_defaults_for_missing_limits(
        self, mock_config, tier_manager, mock_db, mock_user
    ):
        mock_db.query().filter().first.return_value = mock_user
        mock_config.return_value = {}
        limits = tier_manager.get_tier_limits("user123")
        assert limits["daily_verification_limit"] == 100
        assert limits["monthly_verification_limit"] == 3000


class TestUpgradeUserTier:
    def test_upgrades_user_tier(self, tier_manager, mock_db, mock_user):
        mock_db.query().filter().first.return_value = mock_user
        result = tier_manager.upgrade_user_tier("user123", "pro")
        assert result is True
        assert mock_user.subscription_tier == "pro"
        mock_db.commit.assert_called_once()

    def test_upgrades_with_expiry(self, tier_manager, mock_db, mock_user):
        mock_db.query().filter().first.return_value = mock_user
        expires = datetime.now(timezone.utc) + timedelta(days=30)
        result = tier_manager.upgrade_user_tier("user123", "pro", expires)
        assert result is True
        assert mock_user.tier_expires_at == expires

    def test_rejects_invalid_tier(self, tier_manager, mock_db, mock_user):
        mock_db.query().filter().first.return_value = mock_user
        result = tier_manager.upgrade_user_tier("user123", "invalid_tier")
        assert result is False

    def test_returns_false_for_nonexistent_user(self, tier_manager, mock_db):
        mock_db.query().filter().first.return_value = None
        result = tier_manager.upgrade_user_tier("nonexistent", "pro")
        assert result is False


class TestDowngradeUserTier:
    def test_downgrades_to_freemium(self, tier_manager, mock_db, mock_user):
        mock_user.subscription_tier = "pro"
        mock_db.query().filter().first.return_value = mock_user
        result = tier_manager.downgrade_user_tier("user123", "payment_failed")
        assert result is True
        assert mock_user.subscription_tier == "freemium"
        assert mock_user.tier_expires_at is None
        mock_db.commit.assert_called_once()

    def test_returns_false_for_nonexistent_user(self, tier_manager, mock_db):
        mock_db.query().filter().first.return_value = None
        result = tier_manager.downgrade_user_tier("nonexistent")
        assert result is False


class TestCanCreateAPIKey:
    @patch("app.services.tier_manager.TierConfig.get_tier_config")
    def test_denies_api_key_for_zero_limit(
        self, mock_config, tier_manager, mock_db, mock_user
    ):
        mock_db.query().filter().first.return_value = mock_user
        mock_config.return_value = {"api_key_limit": 0}
        can_create, msg = tier_manager.can_create_api_key("user123")
        assert can_create is False
        assert "Pro tier or higher" in msg

    @patch("app.services.tier_manager.TierConfig.get_tier_config")
    def test_allows_unlimited_api_keys(
        self, mock_config, tier_manager, mock_db, mock_user
    ):
        mock_user.subscription_tier = "custom"
        mock_db.query().filter().first.return_value = mock_user
        mock_config.return_value = {"api_key_limit": -1}
        can_create, msg = tier_manager.can_create_api_key("user123")
        assert can_create is True
        assert msg == ""

    @patch("app.services.tier_manager.TierConfig.get_tier_config")
    def test_enforces_api_key_limit(
        self, mock_config, tier_manager, mock_db, mock_user
    ):
        mock_user.subscription_tier = "pro"
        mock_db.query().filter().first.return_value = mock_user
        mock_config.return_value = {"api_key_limit": 2}
        mock_db.query().filter().count.return_value = 2
        can_create, msg = tier_manager.can_create_api_key("user123")
        assert can_create is False
        assert "limit reached" in msg

    @patch("app.services.tier_manager.TierConfig.get_tier_config")
    def test_allows_creation_under_limit(
        self, mock_config, tier_manager, mock_db, mock_user
    ):
        mock_user.subscription_tier = "pro"
        mock_db.query().filter().first.return_value = mock_user
        mock_config.return_value = {"api_key_limit": 5}
        mock_db.query().filter().count.return_value = 3
        can_create, msg = tier_manager.can_create_api_key("user123")
        assert can_create is True


class TestCheckTierHierarchy:
    def test_same_tier_meets_requirement(self, tier_manager):
        assert tier_manager.check_tier_hierarchy("pro", "pro") is True

    def test_higher_tier_meets_requirement(self, tier_manager):
        assert tier_manager.check_tier_hierarchy("custom", "pro") is True

    def test_lower_tier_fails_requirement(self, tier_manager):
        assert tier_manager.check_tier_hierarchy("freemium", "pro") is False

    def test_unknown_tier_defaults_to_zero(self, tier_manager):
        assert tier_manager.check_tier_hierarchy("unknown", "pro") is False
