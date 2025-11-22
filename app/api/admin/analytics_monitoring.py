"""Analytics monitoring endpoints for tracking verification metrics."""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.services.analytics_service import AnalyticsService
from app.services.adaptive_polling import AdaptivePollingService

router = APIRouter(prefix="/analytics", tags=["Analytics"])


@router.get("/success - rate")
async def get_success_rate(
    hours: int = Query(24, ge=1, le=168),
    db: Session = Depends(get_db)
):
    """Get overall verification success rate."""
    metrics = AnalyticsService.get_success_rate(db, hours)
    return {
        "period_hours": hours,
        "metrics": metrics
    }


@router.get("/service/{service}")
async def get_service_metrics(
    service: str,
    hours: int = Query(24, ge=1, le=168),
    db: Session = Depends(get_db)
):
    """Get metrics for specific service."""
    metrics = AnalyticsService.get_service_metrics(db, service, hours)
    return metrics


@router.get("/country/{country}")
async def get_country_metrics(
    country: str,
    hours: int = Query(24, ge=1, le=168),
    db: Session = Depends(get_db)
):
    """Get metrics for specific country."""
    metrics = AnalyticsService.get_country_metrics(db, country, hours)
    return metrics


@router.get("/polling")
async def get_polling_metrics(
    hours: int = Query(24, ge=1, le=168),
    db: Session = Depends(get_db)
):
    """Get SMS polling performance metrics."""
    metrics = AnalyticsService.get_polling_metrics(db, hours)
    return {
        "period_hours": hours,
        "metrics": metrics
    }


@router.get("/polling/optimal - interval")
async def get_optimal_polling_interval(
    service: str = Query(None),
    db: Session = Depends(get_db)
):
    """Get optimal polling interval based on metrics."""
    interval = AdaptivePollingService.get_optimal_interval(db, service)
    return {
        "service": service or "all",
        "optimal_interval_seconds": interval,
        "recommendation": f"Poll every {interval} seconds"
    }


@router.get("/polling/service/{service}/interval")
async def get_service_polling_interval(
    service: str,
    db: Session = Depends(get_db)
):
    """Get service - specific optimized polling interval."""
    interval = AdaptivePollingService.get_service_specific_interval(db, service)
    should_increase = AdaptivePollingService.should_increase_interval(db, service)
    should_decrease = AdaptivePollingService.should_decrease_interval(db, service)

    return {
        "service": service,
        "current_interval_seconds": interval,
        "should_increase": should_increase,
        "should_decrease": should_decrease,
        "recommendation": "Increase interval" if should_increase else ("Decrease interval" if should_decrease else "Optimal")
    }
