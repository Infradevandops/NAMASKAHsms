"""Unit tests for TierManager service."""

from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, patch

import pytest

from app.services.tier_manager import TierManager


class TestGetUserTier:

    def test_returns_freemium_for_unknown_user(self, db):
        tm = TierManager(db)
        assert tm.get_user_tier("nonexistent-id") == "freemium"

    def test_returns_subscription_tier_for_active_user(self, db, regular_user):
        regular_user.subscription_tier = "payg"
        regular_user.tier_expires_at = None
        db.commit()
        tm = TierManager(db)
        assert tm.get_user_tier(regular_user.id) == "payg"

    def test_non_admin_expired_tier_downgrades(self, db, regular_user):
        regular_user.subscription_tier = "pro"
        regular_user.tier_expires_at = datetime.now(timezone.utc) - timedelta(days=1)
        db.commit()
        tm = TierManager(db)
        assert tm.get_user_tier(regular_user.id) == "freemium"
        db.refresh(regular_user)
        assert regular_user.subscription_tier == "freemium"
        assert regular_user.tier_expires_at is None

    def test_admin_tier_never_expires(self, db, admin_user):
        admin_user.subscription_tier = "custom"
        admin_user.tier_expires_at = datetime.now(timezone.utc) - timedelta(days=30)
        db.commit()
        tm = TierManager(db)
        assert tm.get_user_tier(admin_user.id) == "custom"

    def test_active_pro_not_downgraded(self, db, regular_user):
        regular_user.subscription_tier = "pro"
        regular_user.tier_expires_at = datetime.now(timezone.utc) + timedelta(days=15)
        db.commit()
        tm = TierManager(db)
        assert tm.get_user_tier(regular_user.id) == "pro"

    def test_unknown_tier_value_falls_back_to_freemium(self, db, regular_user):
        regular_user.subscription_tier = "enterprise"
        regular_user.tier_expires_at = None
        db.commit()
        tm = TierManager(db)
        assert tm.get_user_tier(regular_user.id) == "freemium"


class TestCanCreateApiKey:

    def test_pro_under_limit_returns_true(self, db, regular_user):
        regular_user.subscription_tier = "pro"
        db.commit()
        tm = TierManager(db)
        can, msg = tm.can_create_api_key(regular_user.id)
        assert can is True
        assert msg == ""

    def test_pro_at_limit_returns_false(self, db, regular_user):
        from app.models.api_key import APIKey
        regular_user.subscription_tier = "pro"
        db.commit()

        # Patch TierConfig to return limit=2 so we don't need 10 DB rows
        with patch("app.services.tier_manager.TierConfig.get_tier_config") as mock_cfg:
            mock_cfg.return_value = {"api_key_limit": 2}
            for i in range(2):
                db.add(APIKey(
                    id=f"key-{i}",
                    user_id=regular_user.id,
                    name=f"k{i}",
                    key_hash=f"hash{i}",
                    key_preview=f"nsk_xxx...{i}",
                    is_active=True,
                    created_at=datetime.now(timezone.utc),
                    expires_at=datetime.now(timezone.utc) + timedelta(days=365),
                    request_count=0,
                ))
            db.commit()
            tm = TierManager(db)
            can, msg = tm.can_create_api_key(regular_user.id)
        assert can is False
        assert "limit reached" in msg

    def test_custom_unlimited_always_true(self, db, regular_user):
        regular_user.subscription_tier = "custom"
        db.commit()
        with patch("app.services.tier_manager.TierConfig.get_tier_config") as mock_cfg:
            mock_cfg.return_value = {"api_key_limit": -1}
            tm = TierManager(db)
            can, msg = tm.can_create_api_key(regular_user.id)
        assert can is True

    def test_freemium_always_false(self, db, regular_user):
        regular_user.subscription_tier = "freemium"
        db.commit()
        with patch("app.services.tier_manager.TierConfig.get_tier_config") as mock_cfg:
            mock_cfg.return_value = {"api_key_limit": 0}
            tm = TierManager(db)
            can, msg = tm.can_create_api_key(regular_user.id)
        assert can is False
