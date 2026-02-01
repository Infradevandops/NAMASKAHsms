

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.api.admin.dependencies import require_admin
from app.core.database import get_db
from app.models.user import User
from app.services.analytics_service import AnalyticsService

router = APIRouter(prefix="/admin/analytics", tags=["admin-analytics"])


@router.get("/overview")
async def get_analytics_overview(current_user: User = Depends(require_admin), db: Session = Depends(get_db)):
    """Get dashboard overview metrics"""
    service = AnalyticsService(db)
    overview = await service.get_overview()
    timeseries = await service.get_timeseries(days=30)
    services = await service.get_services_stats()

    return {"overview": overview, "timeseries": timeseries, "services": services}


@router.get("/timeseries")
async def get_timeseries(
    days: int = 30,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Get timeseries data for charts"""
    service = AnalyticsService(db)
    return await service.get_timeseries(days)


@router.get("/services")
async def get_services_stats(current_user: User = Depends(require_admin), db: Session = Depends(get_db)):
    """Get services breakdown"""
    service = AnalyticsService(db)
    return await service.get_services_stats()