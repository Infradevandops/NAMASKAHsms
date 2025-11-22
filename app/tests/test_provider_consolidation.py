"""Tests for consolidated provider system."""
import pytest
from app.services.provider_system import SMSProvider, ProviderManager
ProviderHealth, ProviderStatus


class MockSMSProvider(SMSProvider):
    """Mock SMS provider for testing."""

    def __init__(self, name: str, should_fail: bool = False):
        super().__init__(name)
        self.should_fail = should_fail
        self.enabled = True

    async def _get_balance(self):
        if self.should_fail:
            raise Exception("Mock balance error")
        return {"balance": 100.0, "currency": "USD"}

    async def _buy_number(self, country: str, service: str):
        if self.should_fail:
            raise Exception("Mock buy error")
        return {
            "activation_id": "12345",
            "phone_number": "+1234567890",
            "cost": 0.50
        }

    async def _check_sms(self, activation_id: str):
        if self.should_fail:
            raise Exception("Mock SMS error")
        return {
            "sms_code": "123456",
            "status": "received"
        }

    async def _get_pricing(self, country: str, service: str):
        if self.should_fail:
            raise Exception("Mock pricing error")
        return {"cost": 0.50, "currency": "USD"}


class TestProviderHealth:
    """Test provider health tracking."""

    def test_health_initialization(self):
        """Test health object initialization."""
        health = ProviderHealth("test_provider")

        assert health.name == "test_provider"
        assert health.status == ProviderStatus.HEALTHY
        assert health.consecutive_failures == 0
        assert health.success_count == 0
        assert health.failure_count == 0
        assert health.is_available()

    def test_record_success(self):
        """Test recording successful operations."""
        health = ProviderHealth("test_provider")

        health.record_success(100.0)

        assert health.success_count == 1
        assert health.consecutive_failures == 0
        assert health.status == ProviderStatus.HEALTHY
        assert health.avg_response_time == 100.0
        assert health.is_available()

    def test_record_failure(self):
        """Test recording failed operations."""
        health = ProviderHealth("test_provider")

        # First failure - should be degraded
        health.record_failure("Test error")
        assert health.failure_count == 1
        assert health.consecutive_failures == 1
        assert health.status == ProviderStatus.DEGRADED
        assert health.last_error == "Test error"
        assert health.is_available()

        # More failures - should become unhealthy
        for i in range(4):
            health.record_failure(f"Error {i}")

        assert health.consecutive_failures == 5
        assert health.status == ProviderStatus.UNHEALTHY
        assert not health.is_available()

    def test_recovery_after_failure(self):
        """Test recovery after failures."""
        health = ProviderHealth("test_provider")

        # Cause failures
        for i in range(3):
            health.record_failure(f"Error {i}")

        assert health.status == ProviderStatus.DEGRADED

        # Record success - should reset consecutive failures
        health.record_success(50.0)

        assert health.consecutive_failures == 0
        assert health.status == ProviderStatus.HEALTHY
        assert health.is_available()


class TestSMSProvider:
    """Test SMS provider base class."""

    @pytest.mark.asyncio
    async def test_successful_operations(self):
        """Test successful provider operations."""
        provider = MockSMSProvider("test_provider")

        # Test balance
        balance = await provider.get_balance()
        assert balance["balance"] == 100.0
        assert provider.health.success_count == 1

        # Test buy number
        result = await provider.buy_number("US", "telegram")
        assert result["activation_id"] == "12345"
        assert provider.health.success_count == 2

        # Test check SMS
        sms = await provider.check_sms("12345")
        assert sms["sms_code"] == "123456"
        assert provider.health.success_count == 3

        # Test pricing
        pricing = await provider.get_pricing("US", "telegram")
        assert pricing["cost"] == 0.50
        assert provider.health.success_count == 4

    @pytest.mark.asyncio
    async def test_failed_operations(self):
        """Test failed provider operations."""
        provider = MockSMSProvider("test_provider", should_fail=True)

        # All operations should fail and record failures
        with pytest.raises(Exception):
            await provider.get_balance()

        with pytest.raises(Exception):
            await provider.buy_number("US", "telegram")

        with pytest.raises(Exception):
            await provider.check_sms("12345")

        with pytest.raises(Exception):
            await provider.get_pricing("US", "telegram")

        # Should have recorded failures
        assert provider.health.failure_count > 0
        assert provider.health.consecutive_failures > 0

    @pytest.mark.asyncio
    async def test_retry_logic(self):
        """Test retry logic with exponential backoff."""
        provider = MockSMSProvider("test_provider", should_fail=True)
        provider.max_retries = 2

        # Should retry and eventually fail
        with pytest.raises(Exception):
            await provider.get_balance()

        # Should have attempted multiple times
        assert provider.health.failure_count >= provider.max_retries

    @pytest.mark.asyncio
    async def test_health_check(self):
        """Test provider health check."""
        # Healthy provider
        provider = MockSMSProvider("healthy_provider")
        is_healthy = await provider.health_check()
        assert is_healthy

        # Unhealthy provider
        provider = MockSMSProvider("unhealthy_provider", should_fail=True)
        is_healthy = await provider.health_check()
        assert not is_healthy


class TestProviderManager:
    """Test provider manager functionality."""

    def test_provider_registration(self):
        """Test registering providers."""
        manager = ProviderManager()
        provider1 = MockSMSProvider("provider1")
        provider2 = MockSMSProvider("provider2")

        manager.register_provider(provider1, is_primary=True, priority=100)
        manager.register_provider(provider2, priority=90)

        assert "provider1" in manager.providers
        assert "provider2" in manager.providers
        assert manager.primary_provider == "provider1"
        assert manager.provider_priority == ["provider1", "provider2"]

    def test_get_available_providers(self):
        """Test getting available providers."""
        manager = ProviderManager()

        # Add enabled provider
        provider1 = MockSMSProvider("enabled_provider")
        provider1.enabled = True
        manager.register_provider(provider1)

        # Add disabled provider
        provider2 = MockSMSProvider("disabled_provider")
        provider2.enabled = False
        manager.register_provider(provider2)

        # Add unhealthy provider
        provider3 = MockSMSProvider("unhealthy_provider")
        provider3.enabled = True
        provider3.health.status = ProviderStatus.UNHEALTHY
        manager.register_provider(provider3)

        available = manager.get_available_providers()
        assert "enabled_provider" in available
        assert "disabled_provider" not in available
        assert "unhealthy_provider" not in available

    def test_get_best_provider(self):
        """Test getting best available provider."""
        manager = ProviderManager()

        provider1 = MockSMSProvider("provider1")
        provider1.enabled = True
        provider2 = MockSMSProvider("provider2")
        provider2.enabled = True

        manager.register_provider(provider1, is_primary=True, priority=100)
        manager.register_provider(provider2, priority=90)

        best = manager.get_best_provider()
        assert best.name == "provider1"  # Should prefer primary

        # Disable primary
        provider1.enabled = False
        best = manager.get_best_provider()
        assert best.name == "provider2"  # Should fallback to next available

    @pytest.mark.asyncio
    async def test_execute_with_failover(self):
        """Test operation execution with failover."""
        manager = ProviderManager()

        # Add failing provider as primary
        failing_provider = MockSMSProvider("failing_provider", should_fail=True)
        failing_provider.enabled = True
        manager.register_provider(failing_provider, is_primary=True, priority=100)

        # Add working provider as backup
        working_provider = MockSMSProvider("working_provider")
        working_provider.enabled = True
        manager.register_provider(working_provider, priority=90)

        # Should failover to working provider
        result = await manager.execute_with_failover("get_balance")
        assert result["balance"] == 100.0

    @pytest.mark.asyncio
    async def test_no_available_providers(self):
        """Test behavior when no providers are available."""
        manager = ProviderManager()

        with pytest.raises(Exception, match="No available providers"):
            await manager.execute_with_failover("get_balance")

    @pytest.mark.asyncio
    async def test_all_providers_fail(self):
        """Test behavior when all providers fail."""
        manager = ProviderManager()

        # Add multiple failing providers
        for i in range(3):
            provider = MockSMSProvider(f"failing_provider_{i}", should_fail=True)
            provider.enabled = True
            manager.register_provider(provider, priority=100 - i)

        with pytest.raises(Exception):
            await manager.execute_with_failover("get_balance")

    @pytest.mark.asyncio
    async def test_specific_provider_sms_check(self):
        """Test checking SMS from specific provider."""
        manager = ProviderManager()

        provider1 = MockSMSProvider("provider1")
        provider1.enabled = True
        provider2 = MockSMSProvider("provider2")
        provider2.enabled = True

        manager.register_provider(provider1)
        manager.register_provider(provider2)

        # Should use specific provider
        result = await manager.check_sms("12345", "provider1")
        assert result["sms_code"] == "123456"

        # Should fallback if provider not specified
        result = await manager.check_sms("12345")
        assert result["sms_code"] == "123456"

    @pytest.mark.asyncio
    async def test_health_check_all(self):
        """Test health checking all providers."""
        manager = ProviderManager()

        provider1 = MockSMSProvider("healthy_provider")
        provider1.enabled = True
        provider2 = MockSMSProvider("unhealthy_provider", should_fail=True)
        provider2.enabled = True

        manager.register_provider(provider1)
        manager.register_provider(provider2)

        results = await manager.health_check_all()

        assert "healthy_provider" in results
        assert "unhealthy_provider" in results
        assert results["healthy_provider"]["healthy"] is True
        assert results["unhealthy_provider"]["healthy"] is False

    def test_get_provider_stats(self):
        """Test getting provider statistics."""
        manager = ProviderManager()

        provider = MockSMSProvider("test_provider")
        provider.enabled = True
        provider.cost_multiplier = 1.5
        manager.register_provider(provider, is_primary=True)

        stats = manager.get_provider_stats()

        assert "providers" in stats
        assert "test_provider" in stats["providers"]
        assert stats["primary_provider"] == "test_provider"
        assert stats["providers"]["test_provider"]["enabled"] is True
        assert stats["providers"]["test_provider"]["cost_multiplier"] == 1.5


class TestProviderIntegration:
    """Integration tests for provider system."""

    @pytest.mark.asyncio
    async def test_complete_verification_flow(self):
        """Test complete verification flow through provider system."""
        manager = ProviderManager()

        provider = MockSMSProvider("test_provider")
        provider.enabled = True
        manager.register_provider(provider, is_primary=True)

        # Check balance
        balance = await manager.get_balance()
        assert balance["balance"] == 100.0

        # Get pricing
        pricing = await manager.get_pricing("US", "telegram")
        assert pricing["cost"] == 0.50

        # Buy number
        purchase = await manager.buy_number("US", "telegram")
        assert purchase["activation_id"] == "12345"

        # Check SMS
        sms = await manager.check_sms("12345")
        assert sms["sms_code"] == "123456"

        # Verify health tracking
        assert provider.health.success_count == 4
        assert provider.health.status == ProviderStatus.HEALTHY

    @pytest.mark.asyncio
    async def test_cost_optimization(self):
        """Test cost optimization features."""
        provider = MockSMSProvider("test_provider")
        provider.cost_multiplier = 0.8  # 20% discount

        pricing = await provider.get_pricing("US", "telegram")

        # Cost should be optimized
        assert pricing["cost"] == 0.40  # 0.50 * 0.8

    @pytest.mark.asyncio
    async def test_provider_priority_ordering(self):
        """Test provider priority ordering."""
        manager = ProviderManager()

        # Add providers in random order with different priorities
        provider_low = MockSMSProvider("low_priority")
        provider_low.enabled = True
        manager.register_provider(provider_low, priority=50)

        provider_high = MockSMSProvider("high_priority")
        provider_high.enabled = True
        manager.register_provider(provider_high, priority=100)

        provider_medium = MockSMSProvider("medium_priority")
        provider_medium.enabled = True
        manager.register_provider(provider_medium, priority=75)

        # Should be ordered by priority
        expected_order = ["high_priority", "medium_priority", "low_priority"]
        assert manager.provider_priority == expected_order

        # Best provider should be highest priority
        best = manager.get_best_provider()
        assert best.name == "high_priority"
