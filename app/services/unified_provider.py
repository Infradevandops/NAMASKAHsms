"""Unified SMS provider interface with retry logic and health checks."""
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from enum import Enum
import asyncio
from app.utils.timezone_utils import utc_now

logger = get_logger(__name__)


class ProviderStatus(Enum):
    """Provider health status."""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"


class ProviderHealth:
    """Track provider health metrics."""

    def __init__(self, name: str):
        self.name = name
        self.status = ProviderStatus.HEALTHY
        self.last_check = utc_now()
        self.success_count = 0
        self.failure_count = 0
        self.last_error = None
        self.response_time_ms = 0

    def record_success(self, response_time_ms: float):
        """Record successful operation."""
        self.success_count += 1
        self.response_time_ms = response_time_ms
        self.last_check = utc_now()
        self._update_status()

    def record_failure(self, error: str):
        """Record failed operation."""
        self.failure_count += 1
        self.last_error = error
        self.last_check = utc_now()
        self._update_status()

    def _update_status(self):
        """Update health status based on metrics."""
        total = self.success_count + self.failure_count
        if total == 0:
            self.status = ProviderStatus.HEALTHY
        else:
            success_rate = self.success_count / total
            if success_rate >= 0.95:
                self.status = ProviderStatus.HEALTHY
            elif success_rate >= 0.80:
                self.status = ProviderStatus.DEGRADED
            else:
                self.status = ProviderStatus.UNHEALTHY

    def is_healthy(self) -> bool:
        """Check if provider is healthy."""
        return self.status in [ProviderStatus.HEALTHY, ProviderStatus.DEGRADED]


class UnifiedSMSProvider(ABC):
    """Unified SMS provider interface."""

    def __init__(self, name: str, max_retries: int = 3, timeout_seconds: int = 30):
        self.name = name
        self.max_retries = max_retries
        self.timeout_seconds = timeout_seconds
        self.health = ProviderHealth(name)

    @abstractmethod
    async def _buy_number(self, country: str, service: str) -> Dict[str, Any]:
        """Implementation - specific buy number logic."""

    @abstractmethod
    async def _check_sms(self, activation_id: str) -> Dict[str, Any]:
        """Implementation - specific check SMS logic."""

    @abstractmethod
    async def _get_balance(self) -> Dict[str, Any]:
        """Implementation - specific get balance logic."""

    async def buy_number(self, country: str, service: str) -> Dict[str, Any]:
        """Buy number with retry logic."""
        for attempt in range(self.max_retries):
            try:
                start = utc_now()
                result = await asyncio.wait_for(
                    self._buy_number(country, service),
                    timeout=self.timeout_seconds
                )
                elapsed = (utc_now() - start).total_seconds() * 1000
                self.health.record_success(elapsed)
                return result
            except asyncio.TimeoutError:
                self.health.record_failure("Timeout")
                if attempt == self.max_retries - 1:
                    raise
                await asyncio.sleep(2 ** attempt)
            except Exception as e:
                self.health.record_failure(str(e))
                if attempt == self.max_retries - 1:
                    raise
                await asyncio.sleep(2 ** attempt)

    async def check_sms(self, activation_id: str) -> Dict[str, Any]:
        """Check SMS with retry logic."""
        for attempt in range(self.max_retries):
            try:
                start = utc_now()
                result = await asyncio.wait_for(
                    self._check_sms(activation_id),
                    timeout=self.timeout_seconds
                )
                elapsed = (utc_now() - start).total_seconds() * 1000
                self.health.record_success(elapsed)
                return result
            except asyncio.TimeoutError:
                self.health.record_failure("Timeout")
                if attempt == self.max_retries - 1:
                    raise
                await asyncio.sleep(2 ** attempt)
            except Exception as e:
                self.health.record_failure(str(e))
                if attempt == self.max_retries - 1:
                    raise
                await asyncio.sleep(2 ** attempt)

    async def get_balance(self) -> Dict[str, Any]:
        """Get balance with retry logic."""
        for attempt in range(self.max_retries):
            try:
                start = utc_now()
                result = await asyncio.wait_for(
                    self._get_balance(),
                    timeout=self.timeout_seconds
                )
                elapsed = (utc_now() - start).total_seconds() * 1000
                self.health.record_success(elapsed)
                return result
            except asyncio.TimeoutError:
                self.health.record_failure("Timeout")
                if attempt == self.max_retries - 1:
                    raise
                await asyncio.sleep(2 ** attempt)
            except Exception as e:
                self.health.record_failure(str(e))
                if attempt == self.max_retries - 1:
                    raise
                await asyncio.sleep(2 ** attempt)

    def get_health(self) -> Dict[str, Any]:
        """Get provider health status."""
        return {
            "name": self.name,
            "status": self.health.status.value,
            "success_rate": self.health.success_count / (self.health.success_count + self.health.failure_count) if (self.health.success_count + self.health.failure_count) > 0 else 0,
            "response_time_ms": self.health.response_time_ms,
            "last_error": self.health.last_error,
            "last_check": self.health.last_check.isoformat()
        }


class ProviderPool:
    """Manage multiple providers with automatic failover."""

    def __init__(self):
        self.providers: Dict[str, UnifiedSMSProvider] = {}
        self.primary_provider: Optional[str] = None

    def register(self, provider: UnifiedSMSProvider, is_primary: bool = False):
        """Register a provider."""
        self.providers[provider.name] = provider
        if is_primary:
            self.primary_provider = provider.name

    async def buy_number(self, country: str, service: str) -> Dict[str, Any]:
        """Buy number with automatic failover."""
        providers_to_try = []

        # Try primary first
        if self.primary_provider:
            providers_to_try.append(self.primary_provider)

        # Then try healthy providers
        for name, provider in self.providers.items():
            if name != self.primary_provider and provider.health.is_healthy():
                providers_to_try.append(name)

        # Finally try unhealthy providers
        for name, provider in self.providers.items():
            if name not in providers_to_try:
                providers_to_try.append(name)

        last_error = None
        for provider_name in providers_to_try:
            try:
                provider = self.providers[provider_name]
                logger.info(f"Attempting buy_number with {provider_name}")
                result = await provider.buy_number(country, service)
                logger.info(f"Successfully bought number from {provider_name}")
                return result
            except Exception as e:
                last_error = e
                logger.warning(f"Provider {provider_name} failed: {e}")
                continue

        raise Exception(f"All providers failed. Last error: {last_error}")

    async def check_sms(self, activation_id: str,
                        provider_name: Optional[str] = None) -> Dict[str, Any]:
        """Check SMS, optionally from specific provider."""
        if provider_name:
            return await self.providers[provider_name].check_sms(activation_id)

        # Try primary provider first
        if self.primary_provider:
            try:
                return await self.providers[self.primary_provider].check_sms(activation_id)
            except Exception:
                pass

        # Failover to other providers
        for name, provider in self.providers.items():
            if name != self.primary_provider:
                try:
                    return await provider.check_sms(activation_id)
                except Exception:
                    continue

        raise Exception("All providers failed to check SMS")

    def get_health_status(self) -> Dict[str, Any]:
        """Get health status of all providers."""
        return {
            provider_name: provider.get_health()
            for provider_name, provider in self.providers.items()
        }


# Global provider pool
provider_pool = ProviderPool()
