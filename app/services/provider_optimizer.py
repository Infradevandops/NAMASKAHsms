"""Provider performance optimization service."""
from typing import Dict
from app.core.logging import get_logger

logger = get_logger(__name__)


class ProviderOptimizer:
    """Optimizes provider selection based on performance."""

    def __init__(self):
        self.provider_stats = {
            "textverified": {"success_rate": 0.95, "cost": 0.50, "latency": 2.0},
            "5sim": {"success_rate": 0.92, "cost": 0.45, "latency": 1.5},
            "getsms": {"success_rate": 0.90, "cost": 0.40, "latency": 2.5},
            "sms - activate": {"success_rate": 0.88, "cost": 0.35, "latency": 3.0}
        }

    async def select_best_provider(
        self,
        country: str,
        service: str,
        priority: str = "success"
    ) -> str:
        """Select best provider based on metrics."""
        if priority == "success":
            return max(
                self.provider_stats.items(),
                key=lambda x: x[1]["success_rate"]
            )[0]
        elif priority == "cost":
            return min(
                self.provider_stats.items(),
                key=lambda x: x[1]["cost"]
            )[0]
        elif priority == "speed":
            return min(
                self.provider_stats.items(),
                key=lambda x: x[1]["latency"]
            )[0]

        return "textverified"  # Default

    async def get_provider_stats(self) -> Dict[str, Dict]:
        """Get provider performance statistics."""
        return self.provider_stats

    async def update_provider_metrics(
        self,
        provider: str,
        success: bool,
        cost: float,
        latency: float
    ):
        """Update provider metrics from real data."""
        if provider in self.provider_stats:
            stats = self.provider_stats[provider]
            # Update with exponential moving average
            alpha = 0.1
            stats["success_rate"] = (
                alpha * (1.0 if success else 0.0)
                + (1 - alpha) * stats["success_rate"]
            )
            stats["cost"] = alpha * cost + (1 - alpha) * stats["cost"]
            stats["latency"] = alpha * latency + (1 - alpha) * stats["latency"]


provider_optimizer = ProviderOptimizer()
