"""Integration tests for SMS provider pool."""
import pytest
from unittest.mock import AsyncMock
from app.services.unified_provider import ProviderPool


class MockProvider(UnifiedSMSProvider):
    """Mock provider for testing."""

    async def _buy_number(self, country: str, service: str):
        return {"activation_id": "123", "phone": "+1234567890"}

    async def _check_sms(self, activation_id: str):
        return {"status": "ok", "sms": "123456"}

    async def _get_balance(self):
        return {"balance": 100.0}


@pytest.mark.asyncio
async def test_provider_pool_registration():
    """Test provider registration."""
    pool = ProviderPool()
    provider = MockProvider("test")

    pool.register(provider, is_primary=True)

    assert "test" in pool.providers
    assert pool.primary_provider == "test"


@pytest.mark.asyncio
async def test_provider_buy_number_success():
    """Test successful number purchase."""
    pool = ProviderPool()
    provider = MockProvider("test")
    pool.register(provider, is_primary=True)

    result = await pool.buy_number("US", "telegram")

    assert result["activation_id"] == "123"
    assert provider.health.success_count > 0


@pytest.mark.asyncio
async def test_provider_failover():
    """Test automatic failover between providers."""
    pool = ProviderPool()

    primary = MockProvider("primary")
    secondary = MockProvider("secondary")

    pool.register(primary, is_primary=True)
    pool.register(secondary)

    # Mock primary to fail
    primary._buy_number = AsyncMock(side_effect=Exception("Primary failed"))

    result = await pool.buy_number("US", "telegram")

    assert result["activation_id"] == "123"
    assert primary.health.failure_count > 0


@pytest.mark.asyncio
async def test_provider_health_tracking():
    """Test provider health tracking."""
    provider = MockProvider("test")

    # Record success
    provider.health.record_success(100.0)
    assert provider.health.status == ProviderStatus.HEALTHY

    # Record failures
    for _ in range(5):
        provider.health.record_failure("Test error")

    assert provider.health.status == ProviderStatus.UNHEALTHY


@pytest.mark.asyncio
async def test_provider_retry_logic():
    """Test retry logic with exponential backoff."""
    provider = MockProvider("test", max_retries=3)

    call_count = 0

    async def failing_buy(*args, **kwargs):
        nonlocal call_count
        call_count += 1
        if call_count < 3:
            raise Exception("Temporary failure")
        return {"activation_id": "123", "phone": "+1234567890"}

    provider._buy_number = failing_buy

    result = await provider.buy_number("US", "telegram")

    assert result["activation_id"] == "123"
    assert call_count == 3


@pytest.mark.asyncio
async def test_provider_timeout():
    """Test timeout handling."""
    provider = MockProvider("test", timeout_seconds=1)

    async def slow_buy(*args, **kwargs):
        import asyncio
        await asyncio.sleep(2)
        return {"activation_id": "123"}

    provider._buy_number = slow_buy

    with pytest.raises(Exception):
        await provider.buy_number("US", "telegram")

    assert provider.health.failure_count > 0


@pytest.mark.asyncio
async def test_check_sms_with_provider():
    """Test checking SMS from specific provider."""
    pool = ProviderPool()
    provider = MockProvider("test")
    pool.register(provider, is_primary=True)

    result = await pool.check_sms("123", provider_name="test")

    assert result["status"] == "ok"
    assert result["sms"] == "123456"


@pytest.mark.asyncio
async def test_get_balance():
    """Test getting provider balance."""
    pool = ProviderPool()
    provider = MockProvider("test")
    pool.register(provider, is_primary=True)

    result = await pool.providers["test"].get_balance()

    assert result["balance"] == 100.0
