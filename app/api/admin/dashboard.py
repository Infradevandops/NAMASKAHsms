"""Enhanced Dashboard API router with comprehensive features."""
from app.core.logging import get_logger
from app.core.dependencies import get_current_user_id
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional

from fastapi import APIRouter, Body, Depends, HTTPException, Query
from sqlalchemy import desc, func
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.user import User
from app.models.verification import Verification, NumberRental
from app.models.transaction import Transaction

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

        # Get user
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

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

        # Active rentals
        active_rentals = (
            db.query(NumberRental)
            .filter(
                NumberRental.user_id == user_id,
                NumberRental.status == "active",
                NumberRental.expires_at > datetime.now(timezone.utc)
            )
            .count()
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
            .order_by(func.count(Verification.id).desc())
            .first()
        )
        popular_service = (
            popular_service_result[0] if popular_service_result else "N/A"
        )

        return {
            "total_verifications": total_verifications,
            "completed_verifications": completed_verifications,
            "active_verifications": active_verifications,
            "success_rate": success_rate,
            "total_spent": float(total_spent),
            "active_rentals": active_rentals,
            "avg_verification_time": avg_verification_time,
            "popular_service": popular_service,
            "period_days": period,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Dashboard stats error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch dashboard stats")


@router.get("/recent-activity")
async def get_recent_activity(
    user_id: str = Depends(get_current_user_id),
    limit: int = Query(10, le=50, description="Number of recent activities"),
    db: Session = Depends(get_db),
):
    """Get recent user activity."""
    try:
        activities = (
            db.query(Verification)
            .filter(Verification.user_id == user_id)
            .order_by(Verification.created_at.desc())
            .limit(limit)
            .all()
        )

        return {
            "activities": [
                {
                    "id": str(v.id),
                    "service": v.service_name,
                    "country": v.country,
                    "status": v.status,
                    "cost": float(v.cost) if v.cost else 0,
                    "created_at": v.created_at.isoformat() if v.created_at else None,
                }
                for v in activities
            ]
        }
    except Exception as e:
        logger.error(f"Recent activity error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch recent activity")


@router.get("/notifications")
async def get_notifications(
    user_id: str = Depends(get_current_user_id),
    unread_only: bool = Query(False, description="Get only unread notifications"),
    db: Session = Depends(get_db),
):
    """Get user notifications."""
    try:
        # Placeholder - notifications table may not exist yet
        return {"notifications": []}
    except Exception as e:
        logger.error(f"Notifications error: {str(e)}")
        return {"notifications": []}


@router.post("/notifications/{notification_id}/mark-read")
async def mark_notification_read(
    notification_id: str,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Mark notification as read."""
    try:
        # Placeholder
        return {"success": True}
    except Exception as e:
        logger.error(f"Mark read error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to mark notification")


@router.get("/pricing")
async def get_service_pricing(
    country: Optional[str] = Query(None, description="Country code"),
    db: Session = Depends(get_db),
):
    """Get current service pricing."""
    try:
        pricing = {
            "telegram": 2.00,
            "whatsapp": 2.50,
            "google": 1.50,
            "facebook": 2.00,
            "instagram": 2.50,
            "twitter": 1.75,
            "tiktok": 2.25,
            "discord": 1.75,
        }
        return {"pricing": pricing}
    except Exception as e:
        logger.error(f"Pricing error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch pricing")


@router.get("/availability")
async def get_service_availability(
    country: Optional[str] = Query(None, description="Country code"),
    db: Session = Depends(get_db),
):
    """Get service availability by country."""
    try:
        availability = {
            "available_services": 35,
            "available_countries": 150,
            "uptime_percentage": 99.9,
        }
        return availability
    except Exception as e:
        logger.error(f"Availability error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch availability")


@router.get("/performance")
async def get_performance_metrics(
    user_id: str = Depends(get_current_user_id),
    period: int = Query(30, description="Period in days"),
    db: Session = Depends(get_db),
):
    """Get user performance metrics."""
    try:
        start_date = datetime.now(timezone.utc) - timedelta(days=period)

        total = (
            db.query(Verification)
            .filter(
                Verification.user_id == user_id, Verification.created_at >= start_date
            )
            .count()
        )
        successful = (
            db.query(Verification)
            .filter(
                Verification.user_id == user_id,
                Verification.created_at >= start_date,
                Verification.status == "completed",
            )
            .count()
        )
        failed = total - successful

        return {
            "total_requests": total,
            "successful": successful,
            "failed": failed,
            "success_rate": (successful / total * 100) if total > 0 else 0,
            "period_days": period,
        }
    except Exception as e:
        logger.error(f"Performance metrics error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch metrics")


@router.put("/preferences")
async def update_preferences(
    preferences: Dict[str, Any] = Body(...),
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Update user preferences."""
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        # Update preferences (placeholder)
        return {"success": True, "preferences": preferences}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Preferences update error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to update preferences")


@router.get("/export")
async def export_data(
    date_from: Optional[datetime] = Query(None),
    date_to: Optional[datetime] = Query(None),
    db: Session = Depends(get_db),
):
    """Export user data."""
    try:
        return {"status": "export_initiated"}
    except Exception as e:
        logger.error(f"Export error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to export data")
