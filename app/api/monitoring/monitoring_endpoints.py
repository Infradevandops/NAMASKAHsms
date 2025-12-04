"""Monitoring and metrics endpoints."""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user_id
from app.core.logging import get_logger
from app.monitoring.payment_metrics import payment_metrics, alert_system

logger = get_logger(__name__)
router = APIRouter(prefix="/api/monitoring", tags=["Monitoring"])


@router.get("/health")
async def system_health():
    """Get system health status.
    
    Returns:
        - status: System health status
        - success_rate: Payment success rate
        - webhook_latency_ms: Average webhook latency
        - total_errors: Total error count
        - alerts: List of active alerts
    """
    try:
        health = payment_metrics.check_health()
        logger.info("System health check completed")
        return health
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Health check failed"
        )


@router.get("/metrics")
async def get_metrics(user_id: str = Depends(get_current_user_id)):
    """Get payment metrics summary.
    
    Returns:
        - total_payments: Total payment count
        - successful_payments: Successful payment count
        - failed_payments: Failed payment count
        - success_rate: Success rate percentage
        - average_payment_amount: Average payment amount
        - average_webhook_latency_ms: Average webhook latency
        - average_response_time_ms: Average response time
        - total_errors: Total error count
        - error_breakdown: Errors by type
        - uptime_seconds: System uptime
    """
    try:
        metrics = payment_metrics.get_summary()
        logger.info("Metrics retrieved")
        return metrics
    except Exception as e:
        logger.error(f"Failed to get metrics: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve metrics"
        )


@router.get("/alerts")
async def get_alerts(user_id: str = Depends(get_current_user_id)):
    """Get active alerts.
    
    Returns:
        - alerts: List of active alerts
        - count: Number of active alerts
    """
    try:
        alerts = alert_system.get_alerts()
        logger.info(f"Retrieved {len(alerts)} alerts")
        return {
            "alerts": alerts,
            "count": len(alerts),
            "timestamp": __import__('datetime').datetime.now(__import__('datetime').timezone.utc).isoformat()
        }
    except Exception as e:
        logger.error(f"Failed to get alerts: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve alerts"
        )


@router.post("/alerts/clear")
async def clear_alerts(user_id: str = Depends(get_current_user_id)):
    """Clear all alerts.
    
    Returns:
        - success: True if cleared
        - message: Confirmation message
    """
    try:
        alert_system.clear_alerts()
        logger.info("Alerts cleared")
        return {
            "success": True,
            "message": "Alerts cleared successfully"
        }
    except Exception as e:
        logger.error(f"Failed to clear alerts: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to clear alerts"
        )


@router.get("/dashboard")
async def monitoring_dashboard(user_id: str = Depends(get_current_user_id)):
    """Get monitoring dashboard data.
    
    Returns:
        - health: System health status
        - metrics: Payment metrics
        - alerts: Active alerts
    """
    try:
        health = payment_metrics.check_health()
        metrics = payment_metrics.get_summary()
        alerts = alert_system.get_alerts()
        
        logger.info("Dashboard data retrieved")
        
        return {
            "health": health,
            "metrics": metrics,
            "alerts": alerts,
            "timestamp": __import__('datetime').datetime.now(__import__('datetime').timezone.utc).isoformat()
        }
    except Exception as e:
        logger.error(f"Failed to get dashboard data: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve dashboard data"
        )
