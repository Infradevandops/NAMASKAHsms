"""Health check endpoints for monitoring."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user_id
from app.core.logging import get_logger
from app.core.textverified_health import get_health_monitor

logger = get_logger(__name__)

router = APIRouter(prefix="/health", tags=["Health"])


@router.get("/textverified")
async def check_textverified_health(
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Check TextVerified API health status.
    
    Returns health metrics including:
    - API connectivity status
    - Response time (ms)
    - Success/error counts
    - Average and p95 response times
    """
    monitor = get_health_monitor()
    health_status = await monitor.check_health()
    
    logger.info(f"Health check requested by user {user_id}: {health_status['status']}")
    
    return {
        "success": True,
        "service": "textverified",
        **health_status,
    }


@router.get("/textverified/metrics")
async def get_textverified_metrics(
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Get TextVerified API metrics.
    
    Returns aggregated metrics:
    - Overall status
    - Success rate
    - Response time statistics
    """
    monitor = get_health_monitor()
    metrics = monitor.get_metrics()
    
    logger.info(f"Metrics requested by user {user_id}: {metrics['status']}")
    
    return {
        "success": True,
        "service": "textverified",
        **metrics,
    }


@router.get("/app")
async def check_app_health(db: Session = Depends(get_db)):
    """Check application health status.
    
    Returns:
    - Database connectivity
    - TextVerified API status
    - Overall application status
    """
    try:
        # Check database
        db.execute("SELECT 1")
        db_status = "healthy"
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        db_status = "unhealthy"

    # Get TextVerified status
    monitor = get_health_monitor()
    tv_metrics = monitor.get_metrics()

    # Determine overall status
    if db_status == "unhealthy" or tv_metrics["status"] == "unhealthy":
        overall_status = "unhealthy"
    elif tv_metrics["status"] == "degraded":
        overall_status = "degraded"
    else:
        overall_status = "healthy"

    return {
        "success": True,
        "status": overall_status,
        "database": db_status,
        "textverified": tv_metrics["status"],
        "textverified_success_rate": tv_metrics["success_rate"],
    }
