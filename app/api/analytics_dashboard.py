"""Analytics dashboard API for monitoring and insights."""
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user_id
from app.core.logging import get_logger
from app.models.user import User
from app.models.verification import Verification

logger = get_logger(__name__)
router = APIRouter(prefix="/analytics", tags=["Analytics"])


@router.get("/dashboard")
async def get_dashboard_analytics(
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Get comprehensive dashboard analytics."""
    try:
        # Get user verifications
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
        failed = sum(1 for v in verifications if v.status in ["failed", "timeout", "cancelled"])
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

        # Recent activity (last 10)
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


@router.get("/top-services")
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


@router.get("/top-countries")
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
