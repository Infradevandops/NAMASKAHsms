"""Admin analytics endpoints."""

import logging
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user_id
from app.models.user import User

logger = logging.getLogger(__name__)
router = APIRouter()


async def require_admin(
    user_id: str = Depends(get_current_user_id), db: Session = Depends(get_db)
):
    """Verify admin access."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user or not user.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")
    return user_id


@router.get("/analytics/overview")
async def get_analytics_overview(
    admin_id: str = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Get analytics overview using the hardened AnalyticsService."""
    try:
        from app.services.analytics_service import AnalyticsService

        service = AnalyticsService(db)
        overview = await service.get_overview()
        refund_stats = await service.get_refund_stats()

        return {
            "overview": overview,
            "refund_stats": refund_stats,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
    except Exception as e:
        logger.error(f"Failed to get analytics overview: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to get analytics")


@router.get("/analytics/timeseries")
async def get_analytics_timeseries(
    days: int = 30,
    admin_id: str = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Get timeseries data for charts."""
    try:
        from app.services.analytics_service import AnalyticsService

        service = AnalyticsService(db)
        return await service.get_timeseries(days=days)
    except Exception as e:
        logger.error(f"Failed to get timeseries data: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to get timeseries")


@router.get("/analytics/services")
async def get_analytics_services(
    admin_id: str = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Get per-service statistics."""
    try:
        from app.services.analytics_service import AnalyticsService

        service = AnalyticsService(db)
        return await service.get_services_stats()
    except Exception as e:
        logger.error(f"Failed to get service stats: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to get service stats")
