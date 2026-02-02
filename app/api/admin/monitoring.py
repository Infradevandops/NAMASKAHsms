"""Advanced monitoring API endpoints."""


from fastapi import APIRouter, BackgroundTasks, Depends
from app.core.dependencies import get_current_admin_user
from app.models.user import User
from app.services.monitoring_service import monitoring_service

router = APIRouter(prefix="/monitoring", tags=["monitoring"])


@router.get("/metrics")
async def get_system_metrics():
    """Get comprehensive system metrics."""
    return await monitoring_service.collect_system_metrics()


@router.get("/health")
async def get_health_report():
    """Get comprehensive health report."""
    return await monitoring_service.generate_health_report()


@router.get("/alerts")
async def check_system_alerts():
    """Check for active system alerts."""
    alerts = await monitoring_service.check_alerts()
    return {"alerts": alerts, "count": len(alerts)}


@router.post("/alerts/test")
async def test_alerting_system(
    background_tasks: BackgroundTasks,
    admin_user: User = Depends(get_current_admin_user),
):
    """Test alerting system (admin only)."""
    # TODO: Implement alerting_service
    return {"message": "Test alert queued"}


@router.get("/sla")
async def get_sla_metrics():
    """Get SLA compliance metrics."""
    health_report = await monitoring_service.generate_health_report()
    return {
        "sla_compliance": health_report["sla_compliance"],
        "uptime": health_report["metrics"]["system"]["uptime"],
        "performance": health_report["metrics"]["performance"],
    }


@router.get("/dashboard")
async def get_monitoring_dashboard():
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