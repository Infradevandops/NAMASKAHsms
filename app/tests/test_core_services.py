"""Unit tests for core services."""
import pytest
from app.services.auth_service import AuthService


@pytest.fixture
def auth_service():
    return AuthService()


class TestAuthService:
    def test_hash_password(self, auth_service):
        password = "test_password_123"
        hashed = auth_service.hash_password(password)
        assert hashed != password
        assert auth_service.verify_password(password, hashed)

    def test_verify_password_fails(self, auth_service):
        password = "test_password_123"
        hashed = auth_service.hash_password(password)
        assert not auth_service.verify_password("wrong_password", hashed)

    def test_create_access_token(self, auth_service):
        user_id = "test_user_123"
        token = auth_service.create_access_token({"sub": user_id})
        assert token is not None
        assert isinstance(token, str)

    def test_decode_token(self, auth_service):
        user_id = "test_user_123"
        token = auth_service.create_access_token({"sub": user_id})
        payload = auth_service.decode_token(token)
        assert payload["sub"] == user_id


class TestVerificationService:
    @pytest.mark.asyncio
    async def test_get_countries(self):
        countries = await provider_manager.get_countries()
        assert isinstance(countries, list)
        assert len(countries) > 0

    @pytest.mark.asyncio
    async def test_get_services(self):
        services = await provider_manager.get_services("US")
        assert isinstance(services, list)


class TestCacheService:
    @pytest.mark.asyncio
    async def test_cache_set_get(self):
        await cache.connect()

        key = "test_key"
        value = "test_value"
        await cache.set(key, value, ttl=60)
        result = await cache.get(key)

        assert result == value
        await cache.disconnect()

    @pytest.mark.asyncio
    async def test_cache_delete(self):
        await cache.connect()

        key = "test_key"
        await cache.set(key, "value", ttl=60)
        await cache.delete(key)
        result = await cache.get(key)

        assert result is None
        await cache.disconnect()
