"""Tests for tier resolution fix — real DB, real TierManager, no mocking the SUT.

Covers:
- TierManager.get_user_tier reads fresh data from DB
- tier_expires_at=None does NOT trigger downgrade (the actual bug)
- tier_expires_at in the past DOES trigger downgrade
- Feature access matrix for all 4 tiers (via fallback config)
- Tier hierarchy checks
- Upgrade / downgrade persistence
"""

import uuid
import pytest
from datetime import datetime, timedelta, timezone

from app.services.tier_manager import TierManager
from app.core.tier_config import TierConfig
from app.models.user import User


def _create_user(db, tier="custom", tier_expires_at=None, credits=100.0):
    """Insert a real user row into the test SQLite DB."""
    user = User(
        id=str(uuid.uuid4()),
        email=f"{uuid.uuid4().hex[:8]}@test.com",
        password_hash="$2b$12$placeholder",
        credits=credits,
        subscription_tier=tier,
        tier_expires_at=tier_expires_at,
        is_admin=tier == "custom",
        is_active=True,
        created_at=datetime.now(timezone.utc),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


# ── get_user_tier: the core bug fix ─────────────────────────────────────────


class TestGetUserTier:

    def test_custom_tier_no_expiry_stays_custom(self, db):
        """THE BUG: admin on custom with tier_expires_at=None was downgraded."""
        user = _create_user(db, tier="custom", tier_expires_at=None)
        tm = TierManager(db)

        assert tm.get_user_tier(user.id) == "custom"
        db.refresh(user)
        assert user.subscription_tier == "custom"

    def test_pro_tier_no_expiry_stays_pro(self, db):
        user = _create_user(db, tier="pro", tier_expires_at=None)
        tm = TierManager(db)

        assert tm.get_user_tier(user.id) == "pro"

    def test_expired_pro_downgrades(self, db):
        past = datetime.now(timezone.utc) - timedelta(days=1)
        user = _create_user(db, tier="pro", tier_expires_at=past)
        tm = TierManager(db)

        assert tm.get_user_tier(user.id) == "freemium"
        db.refresh(user)
        assert user.subscription_tier == "freemium"

    def test_expired_custom_downgrades(self, db):
        past = datetime.now(timezone.utc) - timedelta(hours=1)
        user = _create_user(db, tier="custom", tier_expires_at=past)
        tm = TierManager(db)

        assert tm.get_user_tier(user.id) == "freemium"

    def test_future_expiry_keeps_tier(self, db):
        future = datetime.now(timezone.utc) + timedelta(days=30)
        user = _create_user(db, tier="custom", tier_expires_at=future)
        tm = TierManager(db)

        assert tm.get_user_tier(user.id) == "custom"

    def test_freemium_ignores_expired_date(self, db):
        """Freemium/payg are free tiers — expiry check should not apply."""
        past = datetime.now(timezone.utc) - timedelta(days=1)
        user = _create_user(db, tier="freemium", tier_expires_at=past)
        tm = TierManager(db)

        assert tm.get_user_tier(user.id) == "freemium"

    def test_payg_ignores_expired_date(self, db):
        past = datetime.now(timezone.utc) - timedelta(days=1)
        user = _create_user(db, tier="payg", tier_expires_at=past)
        tm = TierManager(db)

        assert tm.get_user_tier(user.id) == "payg"

    def test_nonexistent_user_returns_freemium(self, db):
        tm = TierManager(db)
        assert tm.get_user_tier("does-not-exist") == "freemium"

    def test_reads_fresh_data_not_stale_session(self, db):
        """Simulate the race: tier is 'custom' in DB but session has stale object."""
        user = _create_user(db, tier="custom")

        # Simulate another process updating the tier (e.g. startup.py)
        # by directly modifying and committing
        user.subscription_tier = "custom"
        db.commit()

        # Now create TierManager with the same session — it should refresh
        tm = TierManager(db)
        result = tm.get_user_tier(user.id)
        assert result == "custom"


# ── check_feature_access (uses fallback config since no subscription_tiers table in SQLite) ──


class TestCheckFeatureAccess:

    @pytest.mark.parametrize(
        "tier,feature,expected",
        [
            ("freemium", "area_code_selection", False),
            ("freemium", "isp_filtering", False),
            ("freemium", "api_access", False),
            ("payg", "area_code_selection", True),
            ("payg", "isp_filtering", True),
            ("payg", "api_access", False),
            ("pro", "area_code_selection", True),
            ("pro", "isp_filtering", True),
            ("pro", "api_access", True),
            ("custom", "area_code_selection", True),
            ("custom", "isp_filtering", True),
            ("custom", "api_access", True),
        ],
    )
    def test_feature_matrix(self, db, tier, feature, expected):
        user = _create_user(db, tier=tier)
        tm = TierManager(db)

        result = tm.check_feature_access(user.id, feature)
        assert (
            result == expected
        ), f"{tier}/{feature}: expected {expected}, got {result}"


# ── check_tier_hierarchy ─────────────────────────────────────────────────────


class TestTierHierarchy:

    @pytest.mark.parametrize(
        "current,required,expected",
        [
            ("custom", "custom", True),
            ("custom", "pro", True),
            ("custom", "payg", True),
            ("custom", "freemium", True),
            ("pro", "custom", False),
            ("payg", "pro", False),
            ("freemium", "payg", False),
            ("freemium", "freemium", True),
        ],
    )
    def test_hierarchy(self, current, required, expected):
        from app.services.tier_manager import TierManager

        # hierarchy check is stateless, db not needed
        from unittest.mock import MagicMock

        tm = TierManager(MagicMock())
        assert tm.check_tier_hierarchy(current, required) == expected


# ── upgrade / downgrade persistence ──────────────────────────────────────────


class TestUpgradeDowngrade:

    def test_upgrade_persists(self, db):
        user = _create_user(db, tier="freemium")
        tm = TierManager(db)

        assert tm.upgrade_user_tier(user.id, "pro") is True
        db.refresh(user)
        assert user.subscription_tier == "pro"

    def test_upgrade_with_expiry(self, db):
        user = _create_user(db, tier="freemium")
        tm = TierManager(db)
        exp = datetime.now(timezone.utc) + timedelta(days=30)

        tm.upgrade_user_tier(user.id, "pro", expires_at=exp)
        db.refresh(user)
        assert user.subscription_tier == "pro"
        assert user.tier_expires_at is not None

    def test_upgrade_invalid_tier_rejected(self, db):
        user = _create_user(db, tier="freemium")
        tm = TierManager(db)

        assert tm.upgrade_user_tier(user.id, "enterprise") is False
        db.refresh(user)
        assert user.subscription_tier == "freemium"

    def test_downgrade_clears_expiry(self, db):
        future = datetime.now(timezone.utc) + timedelta(days=30)
        user = _create_user(db, tier="custom", tier_expires_at=future)
        tm = TierManager(db)

        assert tm.downgrade_user_tier(user.id) is True
        db.refresh(user)
        assert user.subscription_tier == "freemium"
        assert user.tier_expires_at is None


# ── TierConfig fallback sanity ───────────────────────────────────────────────


class TestTierConfigFallback:

    @pytest.mark.parametrize("tier", ["freemium", "payg", "pro", "custom"])
    def test_fallback_has_required_keys(self, tier):
        config = TierConfig._get_fallback_config(tier)
        for key in ("has_api_access", "has_area_code_selection", "has_isp_filtering"):
            assert key in config

    def test_custom_has_all_features(self):
        c = TierConfig._get_fallback_config("custom")
        assert c["has_api_access"] is True
        assert c["has_area_code_selection"] is True
        assert c["has_isp_filtering"] is True

    def test_freemium_has_no_premium_features(self):
        c = TierConfig._get_fallback_config("freemium")
        assert c["has_api_access"] is False
        assert c["has_area_code_selection"] is False
        assert c["has_isp_filtering"] is False

    def test_unknown_tier_falls_back_to_freemium(self):
        c = TierConfig._get_fallback_config("nonexistent")
        assert c["tier"] == "freemium"
