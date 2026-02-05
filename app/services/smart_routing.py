"""Smart SMS routing with AI - based provider selection."""


from datetime import datetime, timedelta
from typing import Dict
from sqlalchemy import case, func
from app.core.database import get_db
from app.models.verification import Verification

class SmartRouter:

    """AI - powered SMS provider routing."""

    def __init__(self):

        self.provider_stats = {}
        self.routing_rules = {
            "cost_weight": 0.3,
            "success_weight": 0.5,
            "speed_weight": 0.2,
        }

    async def select_provider(self, service: str, country: str = "0") -> str:
        """Select optimal provider based on AI analysis."""
        providers = ["5sim", "sms_activate", "getsms", "textverified"]
        scores = {}

        for provider in providers:
            stats = await self._get_provider_stats(provider, service, country)
            scores[provider] = self._calculate_score(stats)

        # Return provider with highest score
        return max(scores, key=scores.get)

    async def _get_provider_stats(self, provider: str, service: str, country: str) -> Dict:
        """Get provider performance statistics."""
        db = next(get_db())

        # Get stats from last 7 days
        week_ago = datetime.utcnow() - timedelta(days=7)

        stats = (
            db.query(
                func.count(Verification.id).label("total"),
                func.avg(Verification.cost).label("avg_cost"),
                func.sum(case((Verification.status == "completed", 1), else_=0)).label("success_count"),
            )
            .filter(
                Verification.provider == provider,
                Verification.service_name == service,
                Verification.created_at >= week_ago,
            )
            .first()
        )

        total = stats.total or 0
        success_rate = (stats.success_count or 0) / max(total, 1)
        avg_cost = stats.avg_cost or 1.0

        return {
            "success_rate": success_rate,
            "avg_cost": avg_cost,
            "total_requests": total,
            "reliability": min(success_rate + (total / 100), 1.0),
        }

    def _calculate_score(self, stats: Dict) -> float:

        """Calculate provider score using weighted metrics."""
        cost_score = 1 / max(stats["avg_cost"], 0.1)  # Lower cost = higher score
        success_score = stats["success_rate"]
        speed_score = stats["reliability"]

        return (
            cost_score * self.routing_rules["cost_weight"]
            + success_score * self.routing_rules["success_weight"]
            + speed_score * self.routing_rules["speed_weight"]
        )


# Global router instance
        smart_router = SmartRouter()
