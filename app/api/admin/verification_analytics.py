"""Admin verification analytics endpoints."""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user_id
from app.models.user import User
from app.services.analytics_service import AnalyticsService

router = APIRouter()


async def require_admin(
    user_id: str = Depends(get_current_user_id), db: Session = Depends(get_db)
):
    """Verify admin access."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user or not user.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")
    return user_id


@router.get("/analytics/verifications/overview")
async def get_verification_overview(
    admin_id: str = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Get high-level verification and revenue metrics."""
    service = AnalyticsService(db)
    return await service.get_overview()


@router.get("/analytics/verifications/timeseries")
async def get_verification_timeseries(
    days: int = Query(30),
    admin_id: str = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Get daily verification and success counts."""
    service = AnalyticsService(db)
    return await service.get_timeseries(days=days)


@router.get("/analytics/verifications/by-service")
async def get_verification_by_service(
    admin_id: str = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Get usage and success rates by service."""
    service = AnalyticsService(db)
    return await service.get_services_stats()


@router.get("/analytics/refunds")
async def get_refund_analytics(
    days: int = Query(30),
    admin_id: str = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Get comprehensive refund analytics."""
    try:
        service = AnalyticsService(db)
        metrics = await service.get_refund_metrics(days)
        return metrics
    except Exception as e:
        from app.core.logging import get_logger
        logger = get_logger(__name__)
        logger.error(f"Failed to get refund analytics: {str(e)}")
        raise HTTPException(
            status_code=500, detail="Failed to retrieve refund analytics"
        )


@router.get("/analytics/revenue/by-service")
async def get_revenue_by_service(
    limit: int = Query(10),
    admin_id: str = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Get net revenue breakdown per service."""
    service = AnalyticsService(db)
    return await service.get_net_revenue_by_service(limit=limit)
