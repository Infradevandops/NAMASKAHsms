"""Analytics service with refactored functions for better maintainability."""
import statistics
from datetime import datetime, timedelta
from typing import List, Dict, Any
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.transaction import Transaction
from app.models.verification import Verification
from app.schemas import (
    ServiceUsage,
    DailyUsage,
    CountryAnalytics,
    TrendData,
    PredictiveInsight,
)
from app.utils.timezone_utils import utc_now


class AnalyticsCalculator:
    """Service class for analytics calculations."""

    def __init__(self, db: Session, user_id: str):
        self.db = db
        self.user_id = user_id

    def get_basic_metrics(self, start_date: datetime) -> Dict[str, Any]:
        """Calculate basic verification metrics."""
        total_verifications = (
            self.db.query(Verification)
            .filter(Verification.user_id == self.user_id, Verification.created_at >= start_date)
            .count()
        )

        completed_verifications = (
            self.db.query(Verification)
            .filter(
                Verification.user_id == self.user_id,
                Verification.created_at >= start_date,
                Verification.status == "completed",
            )
            .count()
        )

        success_rate = (
            (completed_verifications / total_verifications * 100)
            if total_verifications > 0 else 0
        )

        total_spent = (
            self.db.query(func.sum(Transaction.amount))
            .filter(
                Transaction.user_id == self.user_id,
                Transaction.type == "debit",
                Transaction.created_at >= start_date,
            )
            .scalar() or 0
        )

        return {
            "total_verifications": total_verifications,
            "completed_verifications": completed_verifications,
            "success_rate": success_rate,
            "total_spent": total_spent
        }

    def get_service_analytics(self, start_date: datetime) -> List[ServiceUsage]:
        """Calculate service usage analytics."""
        popular_services = (
            self.db.query(Verification.service_name, func.count(Verification.id).label("count"))
            .filter(Verification.user_id == self.user_id, Verification.created_at >= start_date)
            .group_by(Verification.service_name)
            .order_by(func.count(Verification.id).desc())
            .limit(10)
            .all()
        )

        enhanced_services = []
        for service, count in popular_services:
            service_success = (
                self.db.query(Verification)
                .filter(
                    Verification.user_id == self.user_id,
                    Verification.service_name == service,
                    Verification.created_at >= start_date,
                    Verification.status == "completed",
                )
                .count()
            )

            service_cost = (
                self.db.query(func.sum(Verification.cost))
                .filter(
                    Verification.user_id == self.user_id,
                    Verification.service_name == service,
                    Verification.created_at >= start_date,
                )
                .scalar() or 0
            )

            enhanced_services.append(
                ServiceUsage(
                    service=service,
                    count=count,
                    success_rate=round((service_success / count * 100) if count > 0 else 0, 1),
                    avg_cost=round(float(service_cost / count) if count > 0 else 0, 2),
                    total_cost=float(service_cost),
                )
            )

        return enhanced_services

    def get_daily_usage(self, period: int) -> List[DailyUsage]:
        """Calculate daily usage statistics."""
        daily_usage = []
        for i in range(period):
            day = utc_now() - timedelta(days=i)
            day_start = day.replace(hour=0, minute=0, second=0, microsecond=0)
            day_end = day_start + timedelta(days=1)

            day_verifications = (
                self.db.query(Verification)
                .filter(
                    Verification.user_id == self.user_id,
                    Verification.created_at >= day_start,
                    Verification.created_at < day_end,
                )
                .count()
            )

            day_cost = (
                self.db.query(func.sum(Verification.cost))
                .filter(
                    Verification.user_id == self.user_id,
                    Verification.created_at >= day_start,
                    Verification.created_at < day_end,
                )
                .scalar() or 0
            )

            day_success = (
                self.db.query(Verification)
                .filter(
                    Verification.user_id == self.user_id,
                    Verification.created_at >= day_start,
                    Verification.created_at < day_end,
                    Verification.status == "completed",
                )
                .count()
            )

            daily_usage.append(
                DailyUsage(
                    date=day_start.strftime("%Y-%m-%d"),
                    count=day_verifications,
                    cost=float(day_cost),
                    success_rate=round(
                        (day_success / day_verifications * 100) if day_verifications > 0 else 0, 1
                    ),
                )
            )

        return daily_usage

    def get_country_analytics(self, start_date: datetime) -> List[CountryAnalytics]:
        """Calculate country performance analytics."""
        country_stats = (
            self.db.query(
                Verification.country,
                func.count(Verification.id).label("count"),
                func.sum(func.case([(Verification.status == "completed",
                                     1)], else_=0)).label("completed"),
                func.avg(Verification.cost).label("avg_cost"),
            )
            .filter(Verification.user_id == self.user_id, Verification.created_at >= start_date)
            .group_by(Verification.country)
            .all()
        )

        country_analytics = []
        for country, count, completed, avg_cost in country_stats:
            country_analytics.append(
                CountryAnalytics(
                    country=country,
                    count=count,
                    success_rate=round((completed / count * 100) if count > 0 else 0, 1),
                    avg_cost=round(float(avg_cost or 0), 2),
                )
            )

        return country_analytics

    def get_cost_trends(self) -> List[TrendData]:
        """Calculate cost trends over weeks."""
        cost_trends = []
        for i in range(4):
            week_start = utc_now() - timedelta(weeks=i + 1)
            week_end = week_start + timedelta(weeks=1)

            week_cost = (
                self.db.query(func.sum(Verification.cost))
                .filter(
                    Verification.user_id == self.user_id,
                    Verification.created_at >= week_start,
                    Verification.created_at < week_end,
                )
                .scalar() or 0
            )

            cost_trends.append(TrendData(period=f"Week {i + 1}", value=float(week_cost)))

        # Calculate trend changes
        for i in range(len(cost_trends) - 1):
            if cost_trends[i + 1].value > 0:
                change = (
                    (cost_trends[i].value - cost_trends[i + 1].value) / cost_trends[i + 1].value
                ) * 100
                cost_trends[i].change_percent = round(change, 1)

        return cost_trends

    def get_predictions(self, daily_usage: List[DailyUsage]) -> List[PredictiveInsight]:
        """Generate predictive insights."""
        predictions = []
        if len(daily_usage) >= 7:
            recent_usage = [day.count for day in daily_usage[-7:]]
            avg_daily = statistics.mean(recent_usage)

            predictions.append(
                PredictiveInsight(
                    metric="daily_usage",
                    prediction=round(avg_daily * 1.1, 1),
                    confidence=0.75,
                    timeframe="next_week",
                )
            )

            # Cost prediction
            recent_costs = [day.cost for day in daily_usage[-7:]]
            avg_cost = statistics.mean(recent_costs)

            predictions.append(
                PredictiveInsight(
                    metric="weekly_cost",
                    prediction=round(avg_cost * 7 * 1.05, 2),
                    confidence=0.70,
                    timeframe="next_week",
                )
            )

        return predictions

    def calculate_efficiency_score(self, success_rate: float,
                                   total_spent: float, total_verifications: int) -> float:
        """Calculate efficiency score."""
        efficiency_factors = [
            success_rate / 100,
            min(1.0, 50 / (total_spent / total_verifications if total_verifications > 0 else 50)),
            min(1.0, total_verifications / 30),
        ]
        return round(statistics.mean(efficiency_factors) * 100, 1)

    def generate_recommendations(self, success_rate: float, total_spent: float,
                                 total_verifications: int, enhanced_services: List[ServiceUsage]) -> List[str]:
        """Generate recommendations based on analytics."""
        recommendations = []

        if success_rate < 80:
            recommendations.append("Consider switching to higher - success-rate services")

        if total_spent / total_verifications > 1.0 if total_verifications > 0 else False:
            recommendations.append("Look for more cost - effective service options")

        if total_verifications < 10:
            recommendations.append("Increase usage to get better insights")

        if enhanced_services:
            best_service = max(enhanced_services, key=lambda x: x.success_rate)
            recommendations.append(
                f"Consider using {best_service.service} more (highest success rate: {best_service.success_rate}%)"
            )

        return recommendations
