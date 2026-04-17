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
    - SMS Polling service status
    - Refund Policy Enforcer status
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

    # Check SMS Polling Service
    try:
        from app.services.sms_polling_service import sms_polling_service

        polling_status = "healthy" if sms_polling_service.is_running else "unhealthy"
        active_polls = len(sms_polling_service.get_active_polls())
    except Exception as e:
        logger.error(f"Polling service health check failed: {e}")
        polling_status = "unhealthy"
        active_polls = 0

    # Check Refund Policy Enforcer
    try:
        from app.services.refund_policy_enforcer import refund_policy_enforcer

        enforcer_status = (
            "healthy" if refund_policy_enforcer.is_running else "unhealthy"
        )
    except Exception as e:
        logger.error(f"Refund enforcer health check failed: {e}")
        enforcer_status = "unhealthy"

    # Determine overall status
    if (
        db_status == "unhealthy"
        or polling_status == "unhealthy"
        or enforcer_status == "unhealthy"
    ):
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
        "sms_polling": {"status": polling_status, "active_polls": active_polls},
        "refund_enforcer": {
            "status": enforcer_status,
            "interval": "5 minutes",
            "policy": "100% automatic refunds for failed/timeout SMS",
        },
    }
