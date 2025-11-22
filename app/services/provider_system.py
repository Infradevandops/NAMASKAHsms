"""Consolidated SMS provider system with unified interface and management."""
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from enum import Enum
from datetime import datetime
import asyncio
from app.core.logging import get_logger

logger = get_logger(__name__)


class ProviderStatus(str, Enum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"


class ProviderHealth:
    """Track provider health and performance metrics."""

    def __init__(self, name: str):
        self.name = name
        self.status = ProviderStatus.HEALTHY
        self.last_check = datetime.utcnow()
        self.consecutive_failures = 0
        self.success_count = 0
        self.failure_count = 0
        self.last_error: Optional[str] = None
        self.avg_response_time = 0.0

    def record_success(self, response_time_ms: float):
        """Record successful operation."""
        self.success_count += 1
        self.consecutive_failures = 0
        self.last_check = datetime.utcnow()
        self.last_error = None

        # Update average response time
        total_ops = self.success_count + self.failure_count
        self.avg_response_time = ((self.avg_response_time * (total_ops - 1)) + response_time_ms) / total_ops

        self._update_status()

    def record_failure(self, error: str):
        """Record failed operation."""
        self.failure_count += 1
        self.consecutive_failures += 1
        self.last_check = datetime.utcnow()
        self.last_error = error
        self._update_status()

    def _update_status(self):
        """Update health status based on metrics."""
        if self.consecutive_failures >= 5:
            self.status = ProviderStatus.UNHEALTHY
        elif self.consecutive_failures >= 2:
            self.status = ProviderStatus.DEGRADED
        else:
            self.status = ProviderStatus.HEALTHY

    def is_available(self) -> bool:
        """Check if provider is available for operations."""
        return self.status != ProviderStatus.UNHEALTHY


class SMSProvider(ABC):
    """Unified SMS provider interface."""

    def __init__(self, name: str, max_retries: int = 3, timeout: int = 30):
        self.name = name
        self.enabled = False
        self.max_retries = max_retries
        self.timeout = timeout
        self.health = ProviderHealth(name)
        self.cost_multiplier = 1.0

    @abstractmethod
    async def _get_balance(self) -> Dict[str, Any]:
        """Implementation - specific balance check."""

    @abstractmethod
    async def _buy_number(self, country: str, service: str) -> Dict[str, Any]:
        """Implementation - specific number purchase."""

    @abstractmethod
    async def _check_sms(self, activation_id: str) -> Dict[str, Any]:
        """Implementation - specific SMS check."""

    @abstractmethod
    async def _get_pricing(self, country: str, service: str) -> Dict[str, Any]:
        """Implementation - specific pricing."""

    async def execute_with_retry(self, operation, *args, **kwargs) -> Any:
        """Execute operation with retry logic and health tracking."""
        last_error = None

        for attempt in range(self.max_retries):
            try:
                start_time = datetime.utcnow()

                result = await asyncio.wait_for(
                    operation(*args, **kwargs),
                    timeout=self.timeout
                )

                # Record success
                elapsed_ms = (datetime.utcnow() - start_time).total_seconds() * 1000
                self.health.record_success(elapsed_ms)

                return result

            except asyncio.TimeoutError as e:
                last_error = e
                self.health.record_failure(f"Timeout after {self.timeout}s")

            except Exception as e:
                last_error = e
                self.health.record_failure(str(e))

            if attempt < self.max_retries - 1:
                await asyncio.sleep(2 ** attempt)  # Exponential backoff

        raise last_error or Exception(f"All {self.max_retries} attempts failed")

    async def get_balance(self) -> Dict[str, Any]:
        """Get balance with retry logic."""
        return await self.execute_with_retry(self._get_balance)

    async def buy_number(self, country: str, service: str) -> Dict[str, Any]:
        """Buy number with retry logic."""
        return await self.execute_with_retry(self._buy_number, country, service)

    async def check_sms(self, activation_id: str) -> Dict[str, Any]:
        """Check SMS with retry logic."""
        return await self.execute_with_retry(self._check_sms, activation_id)

    async def get_pricing(self, country: str, service: str) -> Dict[str, Any]:
        """Get pricing with retry logic."""
        result = await self.execute_with_retry(self._get_pricing, country, service)

        # Apply cost optimization
        if "cost" in result:
            result["cost"] = result["cost"] * self.cost_multiplier

        return result

    async def health_check(self) -> bool:
        """Perform health check."""
        try:
            await self.get_balance()
            return True
        except Exception as e:
            logger.warning(f"{self.name} health check failed: {e}")
            return False


class ProviderManager:
    """Manage multiple SMS providers with failover and optimization."""

    def __init__(self):
        self.providers: Dict[str, SMSProvider] = {}
        self.primary_provider: Optional[str] = None
        self.provider_priority: List[str] = []

    def register_provider(self, provider: SMSProvider,
                          is_primary: bool = False, priority: int = 100):
        """Register a provider with priority."""
        self.providers[provider.name] = provider

        if is_primary:
            self.primary_provider = provider.name

        # Maintain priority order
        self.provider_priority.append((provider.name, priority))
        self.provider_priority.sort(key=lambda x: x[1], reverse=True)
        self.provider_priority = [name for name, _ in self.provider_priority]

    def get_available_providers(self) -> List[str]:
        """Get list of available providers in priority order."""
        available = []
        for name in self.provider_priority:
            provider = self.providers[name]
            if provider.enabled and provider.health.is_available():
                available.append(name)
        return available

    def get_best_provider(self) -> Optional[SMSProvider]:
        """Get best available provider."""
        available = self.get_available_providers()

        if not available:
            return None

        # Prefer primary if available
        if self.primary_provider and self.primary_provider in available:
            return self.providers[self.primary_provider]

        # Return first available by priority
        return self.providers[available[0]]

    async def execute_with_failover(self, operation_name: str, *args, **kwargs) -> Any:
        """Execute operation with automatic failover."""
        available = self.get_available_providers()

        if not available:
            raise Exception("No available providers")

        last_error = None

        for provider_name in available:
            try:
                provider = self.providers[provider_name]
                operation = getattr(provider, operation_name)

                logger.info(f"Executing {operation_name} on {provider_name}")
                result = await operation(*args, **kwargs)

                logger.info(f"{operation_name} succeeded on {provider_name}")
                return result

            except Exception as e:
                last_error = e
                logger.warning(f"{operation_name} failed on {provider_name}: {e}")
                continue

        raise last_error or Exception(f"All providers failed for {operation_name}")

    async def get_balance(self) -> Dict[str, Any]:
        """Get balance from best provider."""
        return await self.execute_with_failover("get_balance")

    async def buy_number(self, country: str, service: str) -> Dict[str, Any]:
        """Buy number with failover."""
        return await self.execute_with_failover("buy_number", country, service)

    async def check_sms(self, activation_id: str,
                        provider_name: Optional[str] = None) -> Dict[str, Any]:
        """Check SMS from specific or best provider."""
        if provider_name and provider_name in self.providers:
            provider = self.providers[provider_name]
            if provider.enabled and provider.health.is_available():
                return await provider.check_sms(activation_id)

        return await self.execute_with_failover("check_sms", activation_id)

    async def get_pricing(self, country: str, service: str) -> Dict[str, Any]:
        """Get pricing from best provider."""
        return await self.execute_with_failover("get_pricing", country, service)

    async def health_check_all(self) -> Dict[str, Dict[str, Any]]:
        """Health check all providers."""
        results = {}

        for name, provider in self.providers.items():
            try:
                is_healthy = await provider.health_check()
                results[name] = {
                    "enabled": provider.enabled,
                    "healthy": is_healthy,
                    "status": provider.health.status.value,
                    "consecutive_failures": provider.health.consecutive_failures,
                    "success_rate": provider.health.success_count / (provider.health.success_count + provider.health.failure_count) if (provider.health.success_count + provider.health.failure_count) > 0 else 0,
                    "avg_response_time": provider.health.avg_response_time,
                    "last_error": provider.health.last_error
                }
            except Exception as e:
                results[name] = {
                    "enabled": provider.enabled,
                    "healthy": False,
                    "status": ProviderStatus.UNHEALTHY.value,
                    "error": str(e)
                }

        return results

    def get_provider_stats(self) -> Dict[str, Any]:
        """Get comprehensive provider statistics."""
        return {
            "providers": {
                name: {
                    "enabled": provider.enabled,
                    "status": provider.health.status.value,
                    "cost_multiplier": provider.cost_multiplier,
                    "consecutive_failures": provider.health.consecutive_failures,
                    "success_count": provider.health.success_count,
                    "failure_count": provider.health.failure_count,
                    "avg_response_time": provider.health.avg_response_time,
                    "last_check": provider.health.last_check.isoformat()
                }
                for name, provider in self.providers.items()
            },
            "primary_provider": self.primary_provider,
            "available_providers": self.get_available_providers()
        }


# Global provider manager instance
provider_manager = ProviderManager()
