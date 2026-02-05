"""Notification analytics endpoints."""


from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.dependencies import get_current_user_id
from app.core.logging import get_logger
from app.models.user import User
from app.services.notification_analytics_service import NotificationAnalyticsService

logger = get_logger(__name__)
router = APIRouter(prefix="/api/notifications/analytics", tags=["Notification Analytics"])


@router.get("/summary")
async def get_analytics_summary(
    user_id: str = Depends(get_current_user_id),
    notification_type: Optional[str] = Query(None, description="Filter by notification type"),
    days: int = Query(30, ge=1, le=365, description="Number of days to include"),
    db: Session = Depends(get_db),
):
    """Get notification delivery and engagement summary.

    Query Parameters:
        - notification_type: Filter by notification type (optional)
        - days: Number of days to include (1-365, default 30)

    Returns:
        - total_notifications: Total notifications sent
        - sent: Notifications sent
        - delivered: Notifications delivered
        - read: Notifications read
        - clicked: Notifications clicked
        - failed: Notifications failed
        - delivery_rate: Percentage of notifications delivered
        - read_rate: Percentage of delivered notifications read
        - click_rate: Percentage of delivered notifications clicked
        - failure_rate: Percentage of notifications failed
        - avg_delivery_time_ms: Average delivery time in milliseconds
        - avg_read_time_ms: Average read time in milliseconds
        - avg_click_time_ms: Average click time in milliseconds
    """
try:
        # Verify user exists
        user = db.query(User).filter(User.id == user_id).first()
if not user:
            raise HTTPException(status_code=404, detail="User not found")

        service = NotificationAnalyticsService(db)
        metrics = service.get_delivery_metrics(
            user_id=user_id,
            notification_type=notification_type,
            days=days,
        )

        logger.info(f"Analytics summary retrieved for user {user_id}")

        return metrics

except HTTPException:
        raise
except Exception as e:
        logger.error(f"Error retrieving analytics summary: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve analytics summary")


@router.get("/by-type")
async def get_analytics_by_type(
    user_id: str = Depends(get_current_user_id),
    days: int = Query(30, ge=1, le=365, description="Number of days to include"),
    db: Session = Depends(get_db),
):
    """Get notification metrics grouped by notification type.

    Query Parameters:
        - days: Number of days to include (1-365, default 30)

    Returns:
        Dictionary with metrics for each notification type:
        - total: Total notifications of this type
        - delivered: Notifications delivered
        - read: Notifications read
        - clicked: Notifications clicked
        - failed: Notifications failed
        - delivery_rate: Delivery rate percentage
        - read_rate: Read rate percentage
        - click_rate: Click rate percentage
    """
try:
        # Verify user exists
        user = db.query(User).filter(User.id == user_id).first()
if not user:
            raise HTTPException(status_code=404, detail="User not found")

        service = NotificationAnalyticsService(db)
        metrics = service.get_metrics_by_type(user_id=user_id, days=days)

        logger.info(f"Analytics by type retrieved for user {user_id}")

        return metrics

except HTTPException:
        raise
except Exception as e:
        logger.error(f"Error retrieving analytics by type: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve analytics by type")


@router.get("/by-method")
async def get_analytics_by_method(
    user_id: str = Depends(get_current_user_id),
    days: int = Query(30, ge=1, le=365, description="Number of days to include"),
    db: Session = Depends(get_db),
):
    """Get notification metrics grouped by delivery method.

    Query Parameters:
        - days: Number of days to include (1-365, default 30)

    Returns:
        Dictionary with metrics for each delivery method:
        - total: Total notifications via this method
        - delivered: Notifications delivered
        - read: Notifications read
        - clicked: Notifications clicked
        - failed: Notifications failed
        - delivery_rate: Delivery rate percentage
        - read_rate: Read rate percentage
        - click_rate: Click rate percentage
    """
try:
        # Verify user exists
        user = db.query(User).filter(User.id == user_id).first()
if not user:
            raise HTTPException(status_code=404, detail="User not found")

        service = NotificationAnalyticsService(db)
        metrics = service.get_metrics_by_method(user_id=user_id, days=days)

        logger.info(f"Analytics by method retrieved for user {user_id}")

        return metrics

except HTTPException:
        raise
except Exception as e:
        logger.error(f"Error retrieving analytics by method: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve analytics by method")


@router.get("/timeline")
async def get_analytics_timeline(
    user_id: str = Depends(get_current_user_id),
    days: int = Query(30, ge=1, le=365, description="Number of days to include"),
    interval: str = Query("day", description="Time interval: day or hour"),
    db: Session = Depends(get_db),
):
    """Get notification metrics over time.

    Query Parameters:
        - days: Number of days to include (1-365, default 30)
        - interval: Time interval (day or hour, default day)

    Returns:
        List of metrics for each time period:
        - period: Time period (ISO format)
        - total: Total notifications in period
        - delivered: Notifications delivered
        - read: Notifications read
        - clicked: Notifications clicked
        - failed: Notifications failed
        - delivery_rate: Delivery rate percentage
        - read_rate: Read rate percentage
        - click_rate: Click rate percentage
    """
try:
        # Verify user exists
        user = db.query(User).filter(User.id == user_id).first()
if not user:
            raise HTTPException(status_code=404, detail="User not found")

        # Validate interval
if interval not in ["day", "hour"]:
            raise HTTPException(status_code=400, detail="Invalid interval. Must be 'day' or 'hour'")

        service = NotificationAnalyticsService(db)
        metrics = service.get_timeline_metrics(user_id=user_id, days=days, interval=interval)

        logger.info(f"Analytics timeline retrieved for user {user_id}")

        return metrics

except HTTPException:
        raise
except Exception as e:
        logger.error(f"Error retrieving analytics timeline: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve analytics timeline")
