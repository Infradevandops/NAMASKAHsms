import pytest

from app.models.api_key import APIKey
from app.services.api_key_service import APIKeyService


class TestAPIKeyService:
    def test_can_create_key_freemium(self, db_session, regular_user):
        # Freemium has limit 0
        assert APIKeyService.can_create_key(db_session, regular_user.id) is False
        assert APIKeyService.get_remaining_keys(db_session, regular_user.id) == 0

    def test_can_create_key_pro(self, db_session, regular_user):
        # Upgrade to pro
        regular_user.subscription_tier = "pro"
        db_session.commit()

        assert APIKeyService.can_create_key(db_session, regular_user.id) is True
        assert APIKeyService.get_remaining_keys(db_session, regular_user.id) == 10

    def test_create_key_success(self, db_session, regular_user):
        regular_user.subscription_tier = "pro"
        db_session.commit()

        result = APIKeyService.create_key(db_session, regular_user.id, name="Test Key")
        assert "key" in result
        assert result["key"].startswith("sk_")
        assert result["name"] == "Test Key"

        # Count in DB
        count = (
            db_session.query(APIKey).filter(APIKey.user_id == regular_user.id).count()
        )
        assert count == 1
        assert APIKeyService.get_remaining_keys(db_session, regular_user.id) == 9

    def test_create_key_limit_reached(self, db_session, regular_user):
        regular_user.subscription_tier = "pro"
        db_session.commit()

        # Create 10 keys
        for i in range(10):
            APIKeyService.create_key(db_session, regular_user.id, name=f"Key {i}")

        assert APIKeyService.can_create_key(db_session, regular_user.id) is False
        assert APIKeyService.get_remaining_keys(db_session, regular_user.id) == 0

        with pytest.raises(ValueError, match="API key limit reached"):
            APIKeyService.create_key(db_session, regular_user.id)

    def test_custom_tier_unlimited(self, db_session, regular_user):
        regular_user.subscription_tier = "custom"
        db_session.commit()

        assert APIKeyService.can_create_key(db_session, regular_user.id) is True
        assert APIKeyService.get_remaining_keys(db_session, regular_user.id) == 999
