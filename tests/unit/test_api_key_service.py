"""Unit tests for APIKeyService."""

from datetime import datetime, timedelta, timezone
from unittest.mock import patch

import pytest

from app.models.api_key import APIKey
from app.services.api_key_service import APIKeyService


class TestCanCreateKey:

    def test_reads_subscription_tier_not_tier(self, db, regular_user):
        """Regression: must read user.subscription_tier, not user.tier."""
        regular_user.subscription_tier = "pro"
        db.commit()
        with patch(
            "app.services.api_key_service.TierConfig.get_tier_config"
        ) as mock_cfg:
            mock_cfg.return_value = {"api_key_limit": 10}
            service = APIKeyService(db)
            result = service.can_create_key(regular_user.id)
        assert result is True

    def test_can_create_key_uses_tier_config_not_hardcoded(self, db, regular_user):
        """Limit must come from TierConfig, not a local dict."""
        regular_user.subscription_tier = "pro"
        db.commit()
        with patch(
            "app.services.api_key_service.TierConfig.get_tier_config"
        ) as mock_cfg:
            mock_cfg.return_value = {"api_key_limit": 5}
            service = APIKeyService(db)
            assert service.can_create_key(regular_user.id) is True
            mock_cfg.assert_called()

    def test_freemium_cannot_create_key(self, db, regular_user):
        regular_user.subscription_tier = "freemium"
        db.commit()
        with patch(
            "app.services.api_key_service.TierConfig.get_tier_config"
        ) as mock_cfg:
            mock_cfg.return_value = {"api_key_limit": 0}
            service = APIKeyService(db)
            assert service.can_create_key(regular_user.id) is False

    def test_custom_unlimited_can_create(self, db, regular_user):
        regular_user.subscription_tier = "custom"
        db.commit()
        with patch(
            "app.services.api_key_service.TierConfig.get_tier_config"
        ) as mock_cfg:
            mock_cfg.return_value = {"api_key_limit": -1}
            service = APIKeyService(db)
            assert service.can_create_key(regular_user.id) is True


class TestGetRemainingKeys:

    def test_get_remaining_keys_pro(self, db, regular_user):
        regular_user.subscription_tier = "pro"
        db.commit()
        before = (
            db.query(APIKey)
            .filter(APIKey.user_id == regular_user.id, APIKey.is_active.is_(True))
            .count()
        )
        for i in range(3):
            db.add(
                APIKey(
                    id=f"rem-key-{i}-{before}",
                    user_id=regular_user.id,
                    name=f"k{i}",
                    key_hash=f"remhash{i}{before}",
                    key_preview=f"nsk_xxx...{i}",
                    is_active=True,
                    created_at=datetime.now(timezone.utc),
                    expires_at=datetime.now(timezone.utc) + timedelta(days=365),
                    request_count=0,
                )
            )
        db.commit()
        with patch(
            "app.services.api_key_service.TierConfig.get_tier_config"
        ) as mock_cfg:
            mock_cfg.return_value = {"api_key_limit": 10}
            service = APIKeyService(db)
            remaining = service.get_remaining_keys(regular_user.id)
        assert remaining == 10 - (before + 3)

    def test_get_remaining_keys_freemium(self, db, regular_user):
        regular_user.subscription_tier = "freemium"
        db.commit()
        with patch(
            "app.services.api_key_service.TierConfig.get_tier_config"
        ) as mock_cfg:
            mock_cfg.return_value = {"api_key_limit": 0}
            service = APIKeyService(db)
            assert service.get_remaining_keys(regular_user.id) == 0


class TestGenerateApiKey:

    def test_key_prefix_is_nsk(self, db, regular_user):
        regular_user.subscription_tier = "pro"
        db.commit()
        service = APIKeyService(db)
        raw_key, api_key = service.generate_api_key(regular_user.id, name="Test Key")
        assert raw_key.startswith("nsk_")
        assert api_key.name == "Test Key"

    def test_key_saved_to_db(self, db, regular_user):
        regular_user.subscription_tier = "pro"
        db.commit()
        before = db.query(APIKey).filter(APIKey.user_id == regular_user.id).count()
        service = APIKeyService(db)
        service.generate_api_key(regular_user.id, name="My Key")
        after = db.query(APIKey).filter(APIKey.user_id == regular_user.id).count()
        assert after == before + 1


class TestGetUserKeys:

    def test_get_user_keys_excludes_inactive_when_false(self, db, regular_user):
        import uuid

        uid = str(uuid.uuid4())
        db.add(
            APIKey(
                id=f"active-{uid}",
                user_id=regular_user.id,
                name="active",
                key_hash=f"h1-{uid}",
                key_preview="nsk_...",
                is_active=True,
                created_at=datetime.now(timezone.utc),
                expires_at=datetime.now(timezone.utc) + timedelta(days=365),
                request_count=0,
            )
        )
        db.add(
            APIKey(
                id=f"revoked-{uid}",
                user_id=regular_user.id,
                name="revoked",
                key_hash=f"h2-{uid}",
                key_preview="nsk_...",
                is_active=False,
                created_at=datetime.now(timezone.utc),
                expires_at=datetime.now(timezone.utc) + timedelta(days=365),
                request_count=0,
            )
        )
        db.commit()
        service = APIKeyService(db)
        keys = service.get_user_keys(regular_user.id, include_inactive=False)
        assert all(k.is_active for k in keys)
        assert len(keys) >= 1

    def test_get_user_keys_includes_inactive_when_true(self, db, regular_user):
        import uuid

        uid = str(uuid.uuid4())
        db.add(
            APIKey(
                id=f"active2-{uid}",
                user_id=regular_user.id,
                name="active2",
                key_hash=f"h3-{uid}",
                key_preview="nsk_...",
                is_active=True,
                created_at=datetime.now(timezone.utc),
                expires_at=datetime.now(timezone.utc) + timedelta(days=365),
                request_count=0,
            )
        )
        db.add(
            APIKey(
                id=f"revoked2-{uid}",
                user_id=regular_user.id,
                name="revoked2",
                key_hash=f"h4-{uid}",
                key_preview="nsk_...",
                is_active=False,
                created_at=datetime.now(timezone.utc),
                expires_at=datetime.now(timezone.utc) + timedelta(days=365),
                request_count=0,
            )
        )
        db.commit()
        service = APIKeyService(db)
        all_keys = service.get_user_keys(regular_user.id, include_inactive=True)
        active_keys = service.get_user_keys(regular_user.id, include_inactive=False)
        assert len(all_keys) > len(active_keys)


class TestValidateApiKey:

    def test_returns_none_for_expired_key(self, db, regular_user):
        import uuid

        uid = str(uuid.uuid4())
        db.add(
            APIKey(
                id=f"expired-{uid}",
                user_id=regular_user.id,
                name="expired",
                key_hash=f"expiredhash-{uid}",
                key_preview="nsk_...",
                is_active=True,
                created_at=datetime.now(timezone.utc) - timedelta(days=400),
                expires_at=datetime.now(timezone.utc) - timedelta(days=1),
                request_count=0,
            )
        )
        db.commit()
        service = APIKeyService(db)
        assert service.validate_api_key(f"expiredhash-{uid}") is None

    def test_returns_key_for_valid(self, db, regular_user):
        import uuid

        uid = str(uuid.uuid4())
        db.add(
            APIKey(
                id=f"valid-{uid}",
                user_id=regular_user.id,
                name="valid",
                key_hash=f"validhash-{uid}",
                key_preview="nsk_...",
                is_active=True,
                created_at=datetime.now(timezone.utc),
                expires_at=datetime.now(timezone.utc) + timedelta(days=365),
                request_count=0,
            )
        )
        db.commit()
        service = APIKeyService(db)
        result = service.validate_api_key(f"validhash-{uid}")
        assert result is not None
        assert result.id == f"valid-{uid}"

    def test_returns_none_for_revoked_key(self, db, regular_user):
        import uuid

        uid = str(uuid.uuid4())
        db.add(
            APIKey(
                id=f"revoked3-{uid}",
                user_id=regular_user.id,
                name="revoked",
                key_hash=f"revokedhash-{uid}",
                key_preview="nsk_...",
                is_active=False,
                created_at=datetime.now(timezone.utc),
                expires_at=datetime.now(timezone.utc) + timedelta(days=365),
                request_count=0,
            )
        )
        db.commit()
        service = APIKeyService(db)
        assert service.validate_api_key(f"revokedhash-{uid}") is None
