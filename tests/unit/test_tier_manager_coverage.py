"""Tests for TierManager service — targeting coverage gaps."""

import uuid
from datetime import datetime, timedelta, timezone
from unittest.mock import patch

import pytest
from sqlalchemy.orm import Session

from app.models.user import User
from app.services.tier_manager import TierManager


class TestGetUserTier:
    def test_returns_freemium_for_unknown_user(self, db):
        tm = TierManager(db)
        assert tm.get_user_tier("nonexistent") == "freemium"

    def test_returns_user_tier(self, db, test_user):
        tm = TierManager(db)
        assert tm.get_user_tier(test_user.id) == "pro"

    def test_returns_freemium_for_none_tier(self, db):
        uid = str(uuid.uuid4())
        user = User(
            id=uid,
            email=f"{uid[:8]}@test.com",
            password_hash="hash",
            subscription_tier=None,
            created_at=datetime.now(timezone.utc),
        )
        db.add(user)
        db.commit()
        tm = TierManager(db)
        assert tm.get_user_tier(uid) == "freemium"

    def test_admin_bypasses_expiry(self, db, admin_user):
        admin_user.tier_expires_at = datetime.now(timezone.utc) - timedelta(days=30)
        db.commit()
        tm = TierManager(db)
        assert tm.get_user_tier(admin_user.id) == "custom"

    def test_admin_with_no_tier_defaults_custom(self, db):
        uid = str(uuid.uuid4())
        user = User(
            id=uid,
            email=f"{uid[:8]}@test.com",
            password_hash="hash",
            subscription_tier=None,
            is_admin=True,
            created_at=datetime.now(timezone.utc),
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        tm = TierManager(db)
        assert tm.get_user_tier(uid) == "custom"

    def test_expired_pro_downgrades_to_freemium(self, db):
        uid = str(uuid.uuid4())
        user = User(
            id=uid,
            email=f"{uid[:8]}@test.com",
            password_hash="hash",
            subscription_tier="pro",
            is_admin=False,
            tier_expires_at=datetime.now(timezone.utc) - timedelta(days=1),
            created_at=datetime.now(timezone.utc),
        )
        db.add(user)
        db.commit()
        tm = TierManager(db)
        assert tm.get_user_tier(uid) == "freemium"

    def test_non_expired_pro_stays(self, db):
        uid = str(uuid.uuid4())
        user = User(
            id=uid,
            email=f"{uid[:8]}@test.com",
            password_hash="hash",
            subscription_tier="pro",
            is_admin=False,
            tier_expires_at=datetime.now(timezone.utc) + timedelta(days=30),
            created_at=datetime.now(timezone.utc),
        )
        db.add(user)
        db.commit()
        tm = TierManager(db)
        assert tm.get_user_tier(uid) == "pro"

    def test_payg_not_subject_to_expiry(self, db, payg_user):
        tm = TierManager(db)
        assert tm.get_user_tier(payg_user.id) == "payg"

    def test_unknown_tier_falls_back_to_freemium(self, db):
        uid = str(uuid.uuid4())
        user = User(
            id=uid,
            email=f"{uid[:8]}@test.com",
            password_hash="hash",
            subscription_tier="invalid_tier",
            is_admin=False,
            created_at=datetime.now(timezone.utc),
        )
        db.add(user)
        db.commit()
        tm = TierManager(db)
        assert tm.get_user_tier(uid) == "freemium"


class TestCheckFeatureAccess:
    def test_pro_has_api_access(self, db, pro_user):
        tm = TierManager(db)
        assert tm.check_feature_access(pro_user.id, "api_access") is True

    def test_freemium_no_api_access(self, db, regular_user):
        tm = TierManager(db)
        assert tm.check_feature_access(regular_user.id, "api_access") is False

    def test_unknown_feature_returns_false(self, db, pro_user):
        tm = TierManager(db)
        assert tm.check_feature_access(pro_user.id, "nonexistent_feature") is False


class TestGetTierLimits:
    def test_returns_dict_with_limits(self, db, test_user):
        tm = TierManager(db)
        limits = tm.get_tier_limits(test_user.id)
        assert "daily_verification_limit" in limits
        assert "api_key_limit" in limits
        assert "rate_limit_per_minute" in limits


class TestUpgradeUserTier:
    def test_upgrade_success(self, db, regular_user):
        tm = TierManager(db)
        assert tm.upgrade_user_tier(regular_user.id, "payg") is True
        db.refresh(regular_user)
        assert regular_user.subscription_tier == "payg"

    def test_upgrade_with_expiry(self, db, regular_user):
        tm = TierManager(db)
        expires = datetime.now(timezone.utc) + timedelta(days=30)
        assert tm.upgrade_user_tier(regular_user.id, "pro", expires_at=expires) is True
        db.refresh(regular_user)
        assert regular_user.subscription_tier == "pro"
        assert regular_user.tier_expires_at is not None

    def test_upgrade_invalid_tier(self, db, regular_user):
        tm = TierManager(db)
        assert tm.upgrade_user_tier(regular_user.id, "invalid") is False

    def test_upgrade_nonexistent_user(self, db):
        tm = TierManager(db)
        assert tm.upgrade_user_tier("nonexistent", "pro") is False


class TestDowngradeUserTier:
    def test_downgrade_success(self, db, pro_user):
        tm = TierManager(db)
        assert tm.downgrade_user_tier(pro_user.id, "expired") is True
        db.refresh(pro_user)
        assert pro_user.subscription_tier == "freemium"

    def test_downgrade_nonexistent_user(self, db):
        tm = TierManager(db)
        assert tm.downgrade_user_tier("nonexistent") is False


class TestCheckTierHierarchy:
    def test_same_tier(self, db):
        tm = TierManager(db)
        assert tm.check_tier_hierarchy("payg", "payg") is True

    def test_higher_tier(self, db):
        tm = TierManager(db)
        assert tm.check_tier_hierarchy("pro", "payg") is True

    def test_lower_tier(self, db):
        tm = TierManager(db)
        assert tm.check_tier_hierarchy("freemium", "payg") is False

    def test_custom_beats_all(self, db):
        tm = TierManager(db)
        assert tm.check_tier_hierarchy("custom", "pro") is True


class TestCanCreateApiKey:
    def test_freemium_cannot(self, db, regular_user):
        tm = TierManager(db)
        can, msg = tm.can_create_api_key(regular_user.id)
        assert can is False

    def test_pro_can(self, db, pro_user):
        tm = TierManager(db)
        can, msg = tm.can_create_api_key(pro_user.id)
        assert can is True


class TestGetAllTiers:
    def test_returns_list(self, db):
        tm = TierManager(db)
        tiers = tm.get_all_tiers()
        assert isinstance(tiers, list)
