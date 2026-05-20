import logging

logger = logging.getLogger(__name__)
"""Advanced monitoring API endpoints."""

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException

from app.core.dependencies import get_current_admin_user
from app.models.user import User
from app.services.monitoring_service import monitoring_service

router = APIRouter(prefix="/monitoring", tags=["monitoring"])


@router.get("/metrics")
async def get_system_metrics():
    try:
        """Get comprehensive system metrics."""
        return await monitoring_service.collect_system_metrics()
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in get_system_metrics: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/health")
async def get_health_report():
    try:
        """Get comprehensive health report."""
        return await monitoring_service.generate_health_report()
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in get_health_report: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/alerts")
async def check_system_alerts():
    try:
        """Check for active system alerts."""
        alerts = await monitoring_service.check_alerts()
        return {"alerts": alerts, "count": len(alerts)}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in check_system_alerts: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/alerts/test")
async def test_alerting_system(
    background_tasks: BackgroundTasks,
    admin_user: User = Depends(get_current_admin_user),
):
    try:
        """Test alerting system (admin only)."""
        return {
            "message": "Alerting system test not implemented yet",
            "status": "pending",
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in test_alerting_system: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/sla")
async def get_sla_metrics():
    try:
        """Get SLA compliance metrics."""
        health_report = await monitoring_service.generate_health_report()
        return {
            "sla_compliance": health_report["sla_compliance"],
            "uptime": health_report["metrics"]["system"]["uptime"],
            "performance": health_report["metrics"]["performance"],
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in get_sla_metrics: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/dashboard")
async def get_monitoring_dashboard():
    try:
        """Get monitoring dashboard data."""
        metrics = await monitoring_service.collect_system_metrics()
        alerts = await monitoring_service.check_alerts()

        return {
            "overview": {
                "status": "operational" if len(alerts) == 0 else "issues",
                "total_requests": metrics["requests"]["total"],
                "success_rate": metrics["requests"]["success_rate"],
                "avg_response_time": metrics["performance"]["avg_response_time"],
            },
            "metrics": metrics,
            "alerts": alerts,
            "timestamp": metrics["timestamp"],
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in get_monitoring_dashboard: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")
