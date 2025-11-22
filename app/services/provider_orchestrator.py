"""Provider orchestrator with failover and cost optimization."""
from typing import Dict, List, Any, Optional
from enum import Enum
from app.core.logging import get_logger
from app.services.provider_base import UnifiedProviderBase, ProviderStatus

logger = get_logger(__name__)


class FailoverStrategy(str, Enum):
    PRIMARY_ONLY = "primary_only"
    ROUND_ROBIN = "round_robin"
    COST_OPTIMIZED = "cost_optimized"
    HEALTH_AWARE = "health_aware"


class ProviderOrchestrator:
    """Orchestrates multiple providers with failover and optimization."""

    def __init__(self, strategy: FailoverStrategy = FailoverStrategy.HEALTH_AWARE):
        self.providers: Dict[str, UnifiedProviderBase] = {}
        self.primary_provider: Optional[str] = None
        self.strategy = strategy
        self.provider_order: List[str] = []
        self.round_robin_index = 0

    def register_provider(
        self,
        name: str,
        provider: UnifiedProviderBase,
        is_primary: bool = False,
        priority: int = 100
    ):
        """Register a provider with priority."""
        self.providers[name] = provider

        if is_primary:
            self.primary_provider = name

        # Maintain provider order by priority
        self.provider_order.append((name, priority))
        self.provider_order.sort(key=lambda x: x[1], reverse=True)
        self.provider_order = [name for name, _ in self.provider_order]

    def get_available_providers(self) -> List[str]:
        """Get list of available providers."""
        available = []
        for name in self.provider_order:
            provider = self.providers[name]
            if provider.enabled and provider.health.is_available():
                available.append(name)
        return available

    async def get_best_provider(self) -> Optional[UnifiedProviderBase]:
        """Get best provider based on strategy."""
        available = self.get_available_providers()

        if not available:
            logger.error("No available providers")
            return None

        if self.strategy == FailoverStrategy.PRIMARY_ONLY:
            if self.primary_provider in available:
                return self.providers[self.primary_provider]
            return None

        elif self.strategy == FailoverStrategy.ROUND_ROBIN:
            provider_name = available[self.round_robin_index % len(available)]
            self.round_robin_index += 1
            return self.providers[provider_name]

        elif self.strategy == FailoverStrategy.COST_OPTIMIZED:
            # Return provider with lowest cost
            best_provider = None
            best_cost = float('inf')

            for name in available:
                provider = self.providers[name]
                # Use cost multiplier as proxy for cost efficiency
                if provider.cost_multiplier < best_cost:
                    best_cost = provider.cost_multiplier
                    best_provider = provider

            return best_provider

        elif self.strategy == FailoverStrategy.HEALTH_AWARE:
            # Prefer healthy providers, fallback to degraded
            for name in available:
                provider = self.providers[name]
                if provider.health.status == ProviderStatus.HEALTHY:
                    return provider

            # Fallback to degraded
            for name in available:
                provider = self.providers[name]
                if provider.health.status == ProviderStatus.DEGRADED:
                    return provider

            return self.providers[available[0]] if available else None

        return self.providers[available[0]] if available else None

    async def execute_with_failover(
        self,
        operation_name: str,
        *args,
        **kwargs
    ) -> Any:
        """Execute operation with automatic failover."""
        available = self.get_available_providers()

        if not available:
            raise Exception("No available providers for operation")

        last_error = None

        for provider_name in available:
            try:
                provider = self.providers[provider_name]
                operation = getattr(provider, operation_name)

                logger.info(f"Executing {operation_name} on {provider_name}")
                result = await provider.execute_with_retry(operation, *args, **kwargs)

                logger.info(f"{operation_name} succeeded on {provider_name}")
                return result

            except Exception as e:
                last_error = e
                logger.warning(f"{operation_name} failed on {provider_name}: {e}")
                continue

        raise last_error or Exception(f"All providers failed for {operation_name}")

    async def get_balance(self) -> Dict[str, Any]:
        """Get balance from best available provider."""
        provider = await self.get_best_provider()
        if not provider:
            raise Exception("No available providers")

        return await provider.execute_with_retry(provider.get_balance)

    async def buy_number(self, country: str, service: str) -> Dict[str, Any]:
        """Buy number with failover."""
        return await self.execute_with_failover("buy_number", country, service)

    async def check_sms(self, activation_id: str,
                        provider_name: Optional[str] = None) -> Dict[str, Any]:
        """Check SMS from specific or best provider."""
        if provider_name and provider_name in self.providers:
            provider = self.providers[provider_name]
            if provider.enabled:
                return await provider.execute_with_retry(provider.check_sms, activation_id)

        provider = await self.get_best_provider()
        if not provider:
            raise Exception("No available providers")

        return await provider.execute_with_retry(provider.check_sms, activation_id)

    async def get_pricing(self, country: str, service: str) -> Dict[str, Any]:
        """Get pricing from best provider."""
        provider = await self.get_best_provider()
        if not provider:
            raise Exception("No available providers")

        pricing = await provider.execute_with_retry(provider.get_pricing,
                                                    country, service)

        # Apply cost optimization
        if "cost" in pricing:
            pricing["cost"] = provider.apply_cost_optimization(pricing["cost"])

        return pricing

    async def health_check_all(self) -> Dict[str, Dict[str, Any]]:
        """Perform health check on all providers."""
        results = {}

        for name, provider in self.providers.items():
            try:
                is_healthy = await provider.health_check()
                results[name] = {
                    "enabled": provider.enabled,
                    "healthy": is_healthy,
                    "status": provider.health.status.value,
                    "consecutive_failures": provider.health.consecutive_failures,
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
        """Get statistics for all providers."""
        stats = {}

        for name, provider in self.providers.items():
            stats[name] = {
                "enabled": provider.enabled,
                "status": provider.health.status.value,
                "cost_multiplier": provider.cost_multiplier,
                "consecutive_failures": provider.health.consecutive_failures,
                "last_check": provider.health.last_check.isoformat() if provider.health.last_check else None
            }

        return stats
