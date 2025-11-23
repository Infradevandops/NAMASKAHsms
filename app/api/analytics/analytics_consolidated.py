"""Consolidated Analytics API - All analytics endpoints in one module."""
from app.core.dependencies import get_current_user_id
from datetime import datetime, timedelta, timezone
from app.utils.timezone_utils import utc_now
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func

    AnalyticsResponse,
    BusinessMetrics,
    CompetitiveAnalysis,
)

logger = get_logger(__name__)
router = APIRouter(prefix="/analytics", tags=["Analytics"])


@router.get("/usage", response_model=AnalyticsResponse)
def get_user_analytics(
    user_id: str = Depends(get_current_user_id),
    period: int = Query(30, description="Period in days"),
    db: Session = Depends(get_db),
):
    """Get enhanced user analytics with predictions and insights."""
    try:

        calculator = AnalyticsCalculator(db, user_id)
        start_date = utc_now() - timedelta(days=period)

        # Get all analytics components
        basic_metrics = calculator.get_basic_metrics(start_date)
        enhanced_services = calculator.get_service_analytics(start_date)
        daily_usage = calculator.get_daily_usage(period)
        country_analytics = calculator.get_country_analytics(start_date)
        cost_trends = calculator.get_cost_trends()
        predictions = calculator.get_predictions(daily_usage)

        efficiency_score = calculator.calculate_efficiency_score(
            basic_metrics["success_rate"],
            basic_metrics["total_spent"],
            basic_metrics["total_verifications"]
        )

        recommendations = calculator.generate_recommendations(
            basic_metrics["success_rate"],
            basic_metrics["total_spent"],
            basic_metrics["total_verifications"],
            enhanced_services
        )

        return AnalyticsResponse(
            total_verifications=basic_metrics["total_verifications"],
            success_rate=round(basic_metrics["success_rate"], 1),
            total_spent=abs(basic_metrics["total_spent"]),
            popular_services=enhanced_services,
            daily_usage=list(reversed(daily_usage)),
            country_performance=country_analytics,
            cost_trends=cost_trends,
            predictions=predictions,
            efficiency_score=efficiency_score,
            recommendations=recommendations,
        )

    except Exception as e:
        logger.error(f"Analytics error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to load analytics")


@router.get("/dashboard")
async def get_dashboard_analytics(
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Get comprehensive dashboard analytics."""
    try:
        verifications = db.query(Verification).filter(
            Verification.user_id == user_id
        ).all()

        if not verifications:
            return {
                "success": True,
                "summary": {
                    "total_verifications": 0,
                    "successful": 0,
                    "failed": 0,
                    "pending": 0,
                    "success_rate": 0.0,
                    "total_spent": 0.0
                },
                "by_service": {},
                "by_country": {},
                "by_status": {},
                "recent_activity": [],
                "trends": []
            }

        # Summary statistics
        total = len(verifications)
        successful = sum(1 for v in verifications if v.status == "completed")
        failed = sum(1 for v in verifications if v.status in ["failed",
                                                              "timeout", "cancelled"])
        pending = sum(1 for v in verifications if v.status == "pending")
        total_spent = sum(v.cost for v in verifications)
        success_rate = (successful / total * 100) if total > 0 else 0.0

        # By service
        by_service = {}
        for v in verifications:
            service = v.service_name
            if service not in by_service:
                by_service[service] = {"count": 0, "cost": 0.0, "success": 0}
            by_service[service]["count"] += 1
            by_service[service]["cost"] += v.cost
            if v.status == "completed":
                by_service[service]["success"] += 1

        # By country
        by_country = {}
        for v in verifications:
            country = v.country or "Unknown"
            if country not in by_country:
                by_country[country] = {"count": 0, "cost": 0.0, "success": 0}
            by_country[country]["count"] += 1
            by_country[country]["cost"] += v.cost
            if v.status == "completed":
                by_country[country]["success"] += 1

        # By status
        by_status = {
            "completed": successful,
            "failed": failed,
            "pending": pending,
            "cancelled": sum(1 for v in verifications if v.status == "cancelled")
        }

        # Recent activity
        recent = sorted(verifications, key=lambda v: v.created_at, reverse=True)[:10]
        recent_activity = [
            {
                "id": v.id,
                "service": v.service_name,
                "status": v.status,
                "cost": v.cost,
                "created_at": v.created_at.isoformat(),
                "phone": v.phone_number
            }
            for v in recent
        ]

        # Trends (last 30 days)
        thirty_days_ago = datetime.now(timezone.utc) - timedelta(days=30)
        recent_verifications = [v for v in verifications if v.created_at >= thirty_days_ago]

        trends = {}
        for v in recent_verifications:
            date_key = v.created_at.strftime("%Y-%m-%d")
            if date_key not in trends:
                trends[date_key] = {"count": 0, "cost": 0.0, "success": 0}
            trends[date_key]["count"] += 1
            trends[date_key]["cost"] += v.cost
            if v.status == "completed":
                trends[date_key]["success"] += 1

        trends_list = [
            {
                "date": date_key,
                "count": trends[date_key]["count"],
                "cost": round(trends[date_key]["cost"], 2),
                "success": trends[date_key]["success"],
                "success_rate": round(
                    (trends[date_key]["success"] / trends[date_key]["count"] * 100)
                    if trends[date_key]["count"] > 0 else 0,
                    1
                )
            }
            for date_key in sorted(trends.keys())
        ]

        return {
            "success": True,
            "summary": {
                "total_verifications": total,
                "successful": successful,
                "failed": failed,
                "pending": pending,
                "success_rate": round(success_rate, 1),
                "total_spent": round(total_spent, 2)
            },
            "by_service": by_service,
            "by_country": by_country,
            "by_status": by_status,
            "recent_activity": recent_activity,
            "trends": trends_list
        }

    except Exception as e:
        logger.error(f"Dashboard analytics failed: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to load analytics")


@router.get("/summary")
async def get_summary_analytics(
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Get quick summary analytics."""
    try:
        verifications = db.query(Verification).filter(
            Verification.user_id == user_id
        ).all()

        total = len(verifications)
        successful = sum(1 for v in verifications if v.status == "completed")
        total_spent = sum(v.cost for v in verifications)

        # Today's stats
        today = datetime.now(timezone.utc).date()
        today_verifications = [
            v for v in verifications
            if v.created_at.date() == today
        ]
        today_count = len(today_verifications)
        today_successful = sum(1 for v in today_verifications if v.status == "completed")

        return {
            "success": True,
            "total_verifications": total,
            "successful_verifications": successful,
            "success_rate": round((successful / total * 100) if total > 0 else 0, 1),
            "total_spent": round(total_spent, 2),
            "today": {
                "count": today_count,
                "successful": today_successful,
                "success_rate": round((today_successful / today_count * 100) if today_count > 0 else 0, 1)
            }
        }

    except Exception as e:
        logger.error(f"Summary analytics failed: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to load summary")


@router.get("/trends")
async def get_trends(
    user_id: str = Depends(get_current_user_id),
    days: int = Query(30, ge=1, le=365),
    db: Session = Depends(get_db),
):
    """Get verification trends over time."""
    try:
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)
        verifications = db.query(Verification).filter(
            Verification.user_id == user_id,
            Verification.created_at >= cutoff_date
        ).all()

        trends = {}
        for v in verifications:
            date_key = v.created_at.strftime("%Y-%m-%d")
            if date_key not in trends:
                trends[date_key] = {"total": 0, "successful": 0, "cost": 0.0}
            trends[date_key]["total"] += 1
            trends[date_key]["cost"] += v.cost
            if v.status == "completed":
                trends[date_key]["successful"] += 1

        trend_list = [
            {
                "date": date_key,
                "total": trends[date_key]["total"],
                "successful": trends[date_key]["successful"],
                "success_rate": round(
                    (trends[date_key]["successful"] / trends[date_key]["total"] * 100)
                    if trends[date_key]["total"] > 0 else 0,
                    1
                ),
                "cost": round(trends[date_key]["cost"], 2)
            }
            for date_key in sorted(trends.keys())
        ]

        return {
            "success": True,
            "days": days,
            "trends": trend_list
        }

    except Exception as e:
        logger.error(f"Trends failed: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to load trends")


@router.get("/top - services")
async def get_top_services(
    user_id: str = Depends(get_current_user_id),
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db),
):
    """Get top services by usage."""
    try:
        verifications = db.query(Verification).filter(
            Verification.user_id == user_id
        ).all()

        services = {}
        for v in verifications:
            service = v.service_name
            if service not in services:
                services[service] = {"count": 0, "successful": 0, "cost": 0.0}
            services[service]["count"] += 1
            services[service]["cost"] += v.cost
            if v.status == "completed":
                services[service]["successful"] += 1

        # Sort by count and limit
        top_services = sorted(
            services.items(),
            key=lambda x: x[1]["count"],
            reverse=True
        )[:limit]

        return {
            "success": True,
            "services": [
                {
                    "name": name,
                    "count": data["count"],
                    "successful": data["successful"],
                    "success_rate": round(
                        (data["successful"] / data["count"] * 100)
                        if data["count"] > 0 else 0,
                        1
                    ),
                    "total_cost": round(data["cost"], 2)
                }
                for name, data in top_services
            ]
        }

    except Exception as e:
        logger.error(f"Top services failed: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to load top services")


@router.get("/top - countries")
async def get_top_countries(
    user_id: str = Depends(get_current_user_id),
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db),
):
    """Get top countries by usage."""
    try:
        verifications = db.query(Verification).filter(
            Verification.user_id == user_id
        ).all()

        countries = {}
        for v in verifications:
            country = v.country or "Unknown"
            if country not in countries:
                countries[country] = {"count": 0, "successful": 0, "cost": 0.0}
            countries[country]["count"] += 1
            countries[country]["cost"] += v.cost
            if v.status == "completed":
                countries[country]["successful"] += 1

        # Sort by count and limit
        top_countries = sorted(
            countries.items(),
            key=lambda x: x[1]["count"],
            reverse=True
        )[:limit]

        return {
            "success": True,
            "countries": [
                {
                    "name": name,
                    "count": data["count"],
                    "successful": data["successful"],
                    "success_rate": round(
                        (data["successful"] / data["count"] * 100)
                        if data["count"] > 0 else 0,
                        1
                    ),
                    "total_cost": round(data["cost"], 2)
                }
                for name, data in top_countries
            ]
        }

    except Exception as e:
        logger.error(f"Top countries failed: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to load top countries")


@router.get("/business - metrics", response_model=BusinessMetrics)
def get_business_metrics(
    user_id: str = Depends(get_current_user_id),
    period: int = Query(90, description="Period in days"),
    db: Session = Depends(get_db),
):
    """Get business intelligence metrics."""
    try:
        start_date = datetime.now(timezone.utc) - timedelta(days=period)

        revenue = (
            db.query(func.sum(Transaction.amount))
            .filter(
                Transaction.user_id == user_id,
                Transaction.type == "credit",
                Transaction.created_at >= start_date,
            )
            .scalar()
            or 0
        )

        costs = (
            db.query(func.sum(Verification.cost))
            .filter(Verification.user_id == user_id, Verification.created_at >= start_date)
            .scalar()
            or 0
        )

        profit_margin = ((revenue - costs) / revenue * 100) if revenue > 0 else 0

        total_user_spent = (
            db.query(func.sum(Transaction.amount))
            .filter(Transaction.user_id == user_id, Transaction.type == "credit")
            .scalar()
            or 0
        )

        current_month_start = datetime.now(timezone.utc).replace(day=1)
        last_month_start = (current_month_start - timedelta(days=1)).replace(day=1)

        current_month_revenue = (
            db.query(func.sum(Transaction.amount))
            .filter(
                Transaction.user_id == user_id,
                Transaction.type == "credit",
                Transaction.created_at >= current_month_start,
            )
            .scalar()
            or 0
        )

        last_month_revenue = (
            db.query(func.sum(Transaction.amount))
            .filter(
                Transaction.user_id == user_id,
                Transaction.type == "credit",
                Transaction.created_at >= last_month_start,
                Transaction.created_at < current_month_start,
            )
            .scalar()
            or 0
        )

        growth_rate = (
            ((current_month_revenue - last_month_revenue) / last_month_revenue * 100)
            if last_month_revenue > 0
            else 0
        )

        return BusinessMetrics(
            revenue=float(revenue),
            profit_margin=round(profit_margin, 2),
            customer_lifetime_value=float(total_user_spent),
            churn_rate=0.0,
            growth_rate=round(growth_rate, 2),
        )

    except Exception as e:
        logger.error(f"Business metrics error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to load business metrics")


@router.get("/competitive - analysis", response_model=CompetitiveAnalysis)
def get_competitive_analysis(
    country: Optional[str] = Query(None, description="Country code"),
    db: Session = Depends(get_db),
):
    """Get competitive analysis and market positioning."""
    try:
        cost_comparison = {
            "telegram": 0.75,
            "whatsapp": 0.80,
            "google": 0.65,
            "discord": 0.70,
            "instagram": 1.20,
            "facebook": 1.10,
        }

        service_availability = {
            "telegram": True,
            "whatsapp": True,
            "google": True,
            "discord": True,
            "instagram": False,
            "facebook": True,
            "twitter": False,
            "tiktok": True,
        }

        available_services = sum(
            1 for available in service_availability.values() if available
        )
        total_services = len(service_availability)
        performance_benchmark = (available_services / total_services) * 100

        return CompetitiveAnalysis(
            market_position="competitive",
            cost_comparison=cost_comparison,
            service_availability=service_availability,
            performance_benchmark=round(performance_benchmark, 1),
        )

    except Exception as e:
        logger.error(f"Competitive analysis error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to load competitive analysis")


@router.get("/real - time-insights")
def get_real_time_insights(
    user_id: str = Depends(get_current_user_id), db: Session = Depends(get_db)
):
    """Get real - time analytics insights."""
    try:
        now = datetime.now(timezone.utc)
        last_24h = now - timedelta(hours=24)

        recent_verifications = (
            db.query(Verification)
            .filter(Verification.user_id == user_id, Verification.created_at >= last_24h)
            .count()
        )

        recent_success = (
            db.query(Verification)
            .filter(
                Verification.user_id == user_id,
                Verification.created_at >= last_24h,
                Verification.status == "completed",
            )
            .count()
        )

        current_hour = now.replace(minute=0, second=0, microsecond=0)

        hourly_verifications = (
            db.query(Verification)
            .filter(
                Verification.user_id == user_id, Verification.created_at >= current_hour
            )
            .count()
        )

        hourly_services = (
            db.query(Verification.service_name, func.count(Verification.id).label("count"))
            .filter(
                Verification.user_id == user_id, Verification.created_at >= current_hour
            )
            .group_by(Verification.service_name)
            .all()
        )

        return {
            "timestamp": now.isoformat(),
            "last_24h": {
                "verifications": recent_verifications,
                "success_rate": round(
                    (recent_success / recent_verifications * 100)
                    if recent_verifications > 0
                    else 0,
                    1,
                ),
            },
            "current_hour": {
                "verifications": hourly_verifications,
                "services": [{"service": s[0], "count": s[1]} for s in hourly_services],
            },
            "system_status": "operational",
            "alerts": [],
        }

    except Exception as e:
        logger.error(f"Real - time insights error: {str(e)}", exc_info=True)
        return {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "system_status": "degraded",
            "alerts": ["Analytics temporarily unavailable"],
        }
