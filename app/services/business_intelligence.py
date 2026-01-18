"""Business intelligence and analytics service."""

from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timedelta
from typing import Dict, Any
from app.models.rental import Rental


class BusinessIntelligenceService:
    def __init__(self, db: AsyncSession):
        self.db = db

    @async_cache(ttl=3600)
    async def get_revenue_metrics(self, days: int = 30) -> Dict[str, Any]:
        """Get revenue tracking metrics."""
        start_date = datetime.utcnow() - timedelta(days=days)

        query = select(
            func.sum(Rental.cost).label("total_revenue"),
            func.count(Rental.id).label("total_transactions"),
            func.avg(Rental.cost).label("avg_transaction_value"),
        ).where(Rental.created_at >= start_date)

        result = await self.db.execute(query)
        metrics = result.first()

        return {
            "total_revenue": float(metrics.total_revenue or 0),
            "total_transactions": metrics.total_transactions or 0,
            "avg_transaction_value": float(metrics.avg_transaction_value or 0),
            "period_days": days,
        }

    @async_cache(ttl=1800)
    async def get_user_segmentation(self) -> Dict[str, Any]:
        """Get user segmentation data."""
        # Active users (last 30 days)
        active_query = select(func.count(func.distinct(Rental.user_id))).where(
            Rental.created_at >= datetime.utcnow() - timedelta(days=30)
        )
        active_result = await self.db.execute(active_query)
        active_users = active_result.scalar()

        # High - value users (>$10 spent)
        high_value_query = select(func.count(func.distinct(Rental.user_id))).where(
            Rental.user_id.in_(
                select(Rental.user_id).group_by(Rental.user_id).having(func.sum(Rental.cost) > 10)
            )
        )
        high_value_result = await self.db.execute(high_value_query)
        high_value_users = high_value_result.scalar()

        return {
            "active_users_30d": active_users or 0,
            "high_value_users": high_value_users or 0,
            "user_retention_rate": round((active_users / max(high_value_users, 1)) * 100, 2),
        }

    @async_cache(ttl=7200)
    async def get_predictive_analytics(self) -> Dict[str, Any]:
        """Get predictive analytics data."""
        # Revenue trend (last 7 days vs previous 7 days)
        current_week = datetime.utcnow() - timedelta(days=7)
        previous_week = datetime.utcnow() - timedelta(days=14)

        current_revenue_query = select(func.sum(Rental.cost)).where(
            Rental.created_at >= current_week
        )
        current_result = await self.db.execute(current_revenue_query)
        current_revenue = current_result.scalar() or 0

        previous_revenue_query = select(func.sum(Rental.cost)).where(
            and_(Rental.created_at >= previous_week, Rental.created_at < current_week)
        )
        previous_result = await self.db.execute(previous_revenue_query)
        previous_revenue = previous_result.scalar() or 0

        growth_rate = 0
        if previous_revenue > 0:
            growth_rate = ((current_revenue - previous_revenue) / previous_revenue) * 100

        return {
            "weekly_growth_rate": round(growth_rate, 2),
            "current_week_revenue": float(current_revenue),
            "previous_week_revenue": float(previous_revenue),
            "projected_monthly_revenue": float(current_revenue * 4.33),
        }
