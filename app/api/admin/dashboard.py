"""Enhanced Dashboard API router with comprehensive features."""
from app.core.dependencies import get_current_user_id
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional

from fastapi import APIRouter, Body, Depends, HTTPException, Query
from sqlalchemy import desc, func

from app.core.database import get_db

logger = get_logger(__name__)

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@router.get("/stats")
async def get_dashboard_stats(
    user_id: str = Depends(get_current_user_id),
    period: int = Query(30, description="Period in days"),
    db: Session = Depends(get_db),
):
    """Get comprehensive dashboard statistics."""
    try:
        start_date = datetime.now(timezone.utc) - timedelta(days=period)

        # Basic counts
        total_verifications = (
            db.query(Verification)
            .filter(
                Verification.user_id == user_id, Verification.created_at >= start_date
            )
            .count()
        )

        completed_verifications = (
            db.query(Verification)
            .filter(
                Verification.user_id == user_id,
                Verification.created_at >= start_date,
                Verification.status == "completed",
            )
            .count()
        )

        active_verifications = (
            db.query(Verification)
            .filter(Verification.user_id == user_id, Verification.status == "pending")
            .count()
        )

        # Calculate success rate
        success_rate = (
            (completed_verifications / total_verifications * 100)
            if total_verifications > 0
            else 0
        )

        # Total spent
        total_spent = (
            db.query(func.sum(Verification.cost))
            .filter(
                Verification.user_id == user_id, Verification.created_at >= start_date
            )
            .scalar()
            or 0
        )

        # Average verification time (mock for now)
        avg_verification_time = 45  # seconds

        # Most popular service
        popular_service_result = (
            db.query(
                Verification.service_name, func.count(Verification.id).label("count")
            )
            .filter(
                Verification.user_id == user_id, Verification.created_at >= start_date
            )
            .group_by(Verification.service_name)
            .order_by(desc(func.count(Verification.id)))
            .first()
        )

        most_popular_service = (
            popular_service_result[0] if popular_service_result else None
        )

        # Daily usage for the last 7 days
        daily_usage = []
        for i in range(7):
            day = datetime.now(timezone.utc) - timedelta(days=i)
            day_start = day.replace(hour=0, minute=0, second=0, microsecond=0)
            day_end = day_start + timedelta(days=1)

            day_count = (
                db.query(Verification)
                .filter(
                    Verification.user_id == user_id,
                    Verification.created_at >= day_start,
                    Verification.created_at < day_end,
                )
                .count()
            )

            daily_usage.append(
                {"date": day_start.strftime("%Y-%m-%d"), "count": day_count}
            )

        return {
            "total_verifications": total_verifications,
            "completed_verifications": completed_verifications,
            "active_verifications": active_verifications,
            "success_rate": round(success_rate, 1),
            "total_spent": float(total_spent),
            "avg_verification_time": avg_verification_time,
            "most_popular_service": most_popular_service,
            "daily_usage": list(reversed(daily_usage)),
            "period_days": period,
        }

    except Exception as e:
        logger.error("Failed to get dashboard stats: %s", e)
        # Return safe defaults
        return {
            "total_verifications": 0,
            "completed_verifications": 0,
            "active_verifications": 0,
            "success_rate": 0.0,
            "total_spent": 0.0,
            "avg_verification_time": 0,
            "most_popular_service": None,
            "daily_usage": [],
            "period_days": period,
        }


@router.get("/activity/recent")
async def get_recent_activity(
    user_id: str = Depends(get_current_user_id),
    limit: int = Query(10, le=50, description="Number of recent activities"),
    db: Session = Depends(get_db),
):
    """Get recent user activity."""
    try:
        # Get recent verifications
        verifications = (
            db.query(Verification)
            .filter(Verification.user_id == user_id)
            .order_by(desc(Verification.created_at))
            .limit(limit)
            .all()
        )

        activities = []
        for verification in verifications:
            activities.append(
                {
                    "id": verification.id,
                    "type": "verification",
                    "service_name": verification.service_name,
                    "phone_number": verification.phone_number,
                    "status": verification.status,
                    "cost": verification.cost,
                    "capability": verification.capability,
                    "country": verification.country,
                    "created_at": verification.created_at.isoformat(),
                    "completed_at": verification.completed_at.isoformat()
                    if verification.completed_at
                    else None,
                }
            )

        return {"activities": activities}

    except Exception as e:
        logger.error("Failed to get recent activity: %s", e)
        return {"activities": []}


@router.get("/notifications")
async def get_notifications(
    user_id: str = Depends(get_current_user_id),
    unread_only: bool = Query(False, description="Get only unread notifications"),
    db: Session = Depends(get_db),
):
    """Get user notifications."""
    try:
        # For now, return mock notifications
        # In a real implementation, you'd have a notifications table
        notifications = [
            {
                "id": "1",
                "title": "Verification Completed",
                "message": "Your Telegram verification was successful",
                "type": "success",
                "read": False,
                "created_at": datetime.now(timezone.utc).isoformat(),
            }
        ]

        if unread_only:
            notifications = [n for n in notifications if not n["read"]]

        return {
            "notifications": notifications,
            "unread_count": len([n for n in notifications if not n["read"]]),
        }

    except Exception as e:
        logger.error("Failed to get notifications: %s", e)
        return {"notifications": [], "unread_count": 0}


@router.post("/notifications/{notification_id}/read")
async def mark_notification_read(
    notification_id: str,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Mark notification as read."""
    try:
        # In a real implementation, update the notification in the database
        return {"success": True, "message": "Notification marked as read"}

    except Exception as e:
        logger.error("Failed to mark notification as read: %s", e)
        raise HTTPException(status_code=500, detail="Failed to update notification")


@router.get("/services/pricing")
async def get_service_pricing(
    country: Optional[str] = Query(None, description="Country code"),
    db: Session = Depends(get_db),
):
    """Get current service pricing."""
    try:
        # Base pricing (would be dynamic in real implementation)
        base_pricing = {
            "telegram": {"sms": 0.50, "voice": 0.80},
            "whatsapp": {"sms": 0.60, "voice": 0.90},
            "google": {"sms": 0.40, "voice": 0.70},
            "discord": {"sms": 0.50, "voice": 0.80},
            "instagram": {"sms": 0.80, "voice": 1.10},
            "facebook": {"sms": 0.70, "voice": 1.00},
            "twitter": {"sms": 0.75, "voice": 1.05},
            "tiktok": {"sms": 0.85, "voice": 1.15},
        }

        # Country multipliers
        country_multipliers = {
            "US": 1.0,
            "GB": 1.0,
            "CA": 1.1,
            "AU": 1.4,
            "DE": 1.0,
            "FR": 1.0,
            "IN": 0.3,
            "BR": 0.4,
        }

        multiplier = country_multipliers.get(country, 1.0) if country else 1.0

        # Apply country multiplier
        pricing = {}
        for service, prices in base_pricing.items():
            pricing[service] = {
                "sms": round(prices["sms"] * multiplier, 2),
                "voice": round(prices["voice"] * multiplier, 2),
            }

        return {
            "pricing": pricing,
            "country": country,
            "multiplier": multiplier,
            "currency": "USD",
        }

    except Exception as e:
        logger.error("Failed to get service pricing: %s", e)
        raise HTTPException(status_code=500, detail="Failed to get pricing")


@router.get("/services/availability")
async def get_service_availability(
    country: Optional[str] = Query(None, description="Country code"),
    db: Session = Depends(get_db),
):
    """Get service availability by country."""
    try:
        # Mock availability data (would be real - time in production)
        availability = {
            "telegram": {"available": True, "stock": "high", "eta": "instant"},
            "whatsapp": {"available": True, "stock": "medium", "eta": "1 - 2 min"},
            "google": {"available": True, "stock": "high", "eta": "instant"},
            "discord": {"available": True, "stock": "high", "eta": "instant"},
            "instagram": {"available": True, "stock": "low", "eta": "2 - 5 min"},
            "facebook": {"available": True, "stock": "medium", "eta": "1 - 3 min"},
            "twitter": {"available": False, "stock": "none", "eta": "unavailable"},
            "tiktok": {"available": True, "stock": "medium", "eta": "1 - 2 min"},
        }

        return {
            "availability": availability,
            "country": country,
            "last_updated": datetime.now(timezone.utc).isoformat(),
        }

    except Exception as e:
        logger.error("Failed to get service availability: %s", e)
        raise HTTPException(status_code=500, detail="Failed to get availability")


@router.get("/performance")
async def get_performance_metrics(
    user_id: str = Depends(get_current_user_id),
    period: int = Query(30, description="Period in days"),
    db: Session = Depends(get_db),
):
    """Get user performance metrics."""
    try:
        start_date = datetime.now(timezone.utc) - timedelta(days=period)

        # Service performance
        service_performance = (
            db.query(
                Verification.service_name,
                func.count(Verification.id).label("total"),
                func.sum(
                    func.case([(Verification.status == "completed", 1)], else_=0)
                ).label("completed"),
                func.avg(Verification.cost).label("avg_cost"),
            )
            .filter(
                Verification.user_id == user_id, Verification.created_at >= start_date
            )
            .group_by(Verification.service_name)
            .all()
        )

        performance_data = []
        for service, total, completed, avg_cost in service_performance:
            success_rate = (completed / total * 100) if total > 0 else 0
            performance_data.append(
                {
                    "service": service,
                    "total_verifications": total,
                    "completed_verifications": completed or 0,
                    "success_rate": round(success_rate, 1),
                    "avg_cost": round(float(avg_cost or 0), 2),
                }
            )

        # Country performance
        country_performance = (
            db.query(
                Verification.country,
                func.count(Verification.id).label("total"),
                func.sum(
                    func.case([(Verification.status == "completed", 1)], else_=0)
                ).label("completed"),
            )
            .filter(
                Verification.user_id == user_id, Verification.created_at >= start_date
            )
            .group_by(Verification.country)
            .all()
        )

        country_data = []
        for country, total, completed in country_performance:
            success_rate = (completed / total * 100) if total > 0 else 0
            country_data.append(
                {
                    "country": country,
                    "total_verifications": total,
                    "success_rate": round(success_rate, 1),
                }
            )

        return {
            "service_performance": performance_data,
            "country_performance": country_data,
            "period_days": period,
        }

    except Exception as e:
        logger.error("Failed to get performance metrics: %s", e)
        return {
            "service_performance": [],
            "country_performance": [],
            "period_days": period,
        }


@router.post("/preferences")
async def update_user_preferences(
    preferences: Dict[str, Any] = Body(...),
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Update user preferences."""
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        # In a real implementation, you'd have a preferences table or JSON column
        # For now, we'll just return success

        return SuccessResponse(
            message="Preferences updated successfully", data=preferences
        )

    except Exception as e:
        logger.error("Failed to update preferences: %s", e)
        raise HTTPException(status_code=500, detail="Failed to update preferences")


@router.get("/export")
async def export_user_data(
    user_id: str = Depends(get_current_user_id),
    data_type: str = Query("verifications", description="Data type to export"),
    format_type: str = Query("json", description="Export format"),
    date_from: Optional[datetime] = Query(None),
    date_to: Optional[datetime] = Query(None),
    db: Session = Depends(get_db),
):
    """Export user data."""
    try:
        if not date_from:
            date_from = datetime.now(timezone.utc) - timedelta(days=90)
        if not date_to:
            date_to = datetime.now(timezone.utc)

        if data_type == "verifications":
            verifications = (
                db.query(Verification)
                .filter(
                    Verification.user_id == user_id,
                    Verification.created_at >= date_from,
                    Verification.created_at <= date_to,
                )
                .order_by(desc(Verification.created_at))
                .all()
            )

            data = []
            for v in verifications:
                data.append(
                    {
                        "id": v.id,
                        "service_name": v.service_name,
                        "phone_number": v.phone_number,
                        "status": v.status,
                        "cost": v.cost,
                        "capability": v.capability,
                        "country": v.country,
                        "created_at": v.created_at.isoformat(),
                        "completed_at": v.completed_at.isoformat()
                        if v.completed_at
                        else None,
                    }
                )

        elif data_type == "transactions":
            transactions = (
                db.query(Transaction)
                .filter(
                    Transaction.user_id == user_id,
                    Transaction.created_at >= date_from,
                    Transaction.created_at <= date_to,
                )
                .order_by(desc(Transaction.created_at))
                .all()
            )

            data = []
            for t in transactions:
                data.append(
                    {
                        "id": t.id,
                        "amount": t.amount,
                        "type": t.type,
                        "description": t.description,
                        "created_at": t.created_at.isoformat(),
                    }
                )

        else:
            raise HTTPException(status_code=400, detail="Invalid data type")

        return {
            "data": data,
            "format": format_type,
            "count": len(data),
            "date_range": {"from": date_from.isoformat(), "to": date_to.isoformat()},
            "exported_at": datetime.now(timezone.utc).isoformat(),
        }

    except Exception as e:
        logger.error("Failed to export data: %s", e)
        raise HTTPException(status_code=500, detail="Failed to export data")


@router.get("/health")
async def get_dashboard_health():
    """Get dashboard health status."""
    try:
        return {
            "status": "healthy",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "version": "2.0.0",
            "features": {
                "real_time_updates": True,
                "notifications": True,
                "analytics": True,
                "export": True,
            },
        }
    except Exception as e:
        logger.error("Dashboard health check failed: %s", e)
        return {
            "status": "degraded",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "error": str(e),
        }
