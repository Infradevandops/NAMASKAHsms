"""
Free Enhanced Monitoring Endpoints
- System health dashboard
- Real-time metrics
- Service status checks
- Alert thresholds
"""

import asyncio
import os
import platform
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

import psutil
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, text
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.database import get_db, test_database_connection
from app.core.logging import get_logger
from app.models.transaction import PaymentLog, Transaction
from app.models.user import User
from app.models.verification import Verification

router = APIRouter(prefix="/api/monitoring", tags=["Monitoring"])
logger = get_logger(__name__)
settings = get_settings()

# Alert thresholds
THRESHOLDS = {
    "memory_percent": 85,
    "disk_percent": 90,
    "cpu_percent": 90,
    "db_response_ms": 500,
    "redis_response_ms": 100,
    "textverified_balance": 5.0,
}


@router.get("/health/detailed")
async def detailed_health_check(db: Session = Depends(get_db)) -> Dict[str, Any]:
    """Comprehensive health check with all service statuses."""
    checks = {}
    alerts = []

    # 1. Database health
    try:
        start = datetime.now()
        db.execute(text("SELECT 1"))
        db_latency = (datetime.now() - start).total_seconds() * 1000
        checks["database"] = {
            "status": "healthy",
            "latency_ms": round(db_latency, 2),
        }
        if db_latency > THRESHOLDS["db_response_ms"]:
            alerts.append(f"Database latency high: {db_latency:.0f}ms")
    except Exception as e:
        checks["database"] = {"status": "unhealthy", "error": str(e)}
        alerts.append("Database connection failed")

    # 2. Redis/Cache health
    try:
        from app.core.unified_cache import cache

        start = datetime.now()
        await cache.set("health_check", "ok", ttl=10)
        result = await cache.get("health_check")
        redis_latency = (datetime.now() - start).total_seconds() * 1000
        backend = "redis" if cache.redis_client else "memory"
        checks["cache"] = {
            "status": "healthy" if result == "ok" else "degraded",
            "latency_ms": round(redis_latency, 2),
            "backend": backend,
        }
    except Exception as e:
        checks["cache"] = {"status": "unhealthy", "error": str(e), "backend": "unknown"}
        alerts.append("Cache connection failed")

    # 3. TextVerified provider health
    try:
        from app.services.textverified_service import TextVerifiedService

        tv = TextVerifiedService()
        if tv.enabled:
            balance_data = await tv.get_balance()
            balance = (
                float(balance_data)
                if not isinstance(balance_data, dict)
                else float(balance_data.get("balance", balance_data.get("credits", 0)))
            )
            checks["textverified"] = {
                "status": (
                    "healthy"
                    if balance > THRESHOLDS["textverified_balance"]
                    else "warning"
                ),
                "balance": f"${balance:.2f}",
                "enabled": True,
            }
            if balance <= THRESHOLDS["textverified_balance"]:
                alerts.append(f"TextVerified balance low: ${balance:.2f}")
        else:
            checks["textverified"] = {"status": "disabled", "enabled": False}
            alerts.append("TextVerified is disabled")
    except Exception as e:
        checks["textverified"] = {"status": "error", "error": str(e)}
        alerts.append(f"TextVerified check failed: {e}")

    # 4. System resources
    try:
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage("/")
        cpu = psutil.cpu_percent(interval=0.1)

        checks["system"] = {
            "status": "healthy",
            "memory": {
                "percent": memory.percent,
                "used_gb": round(memory.used / (1024**3), 2),
                "total_gb": round(memory.total / (1024**3), 2),
            },
            "disk": {
                "percent": disk.percent,
                "used_gb": round(disk.used / (1024**3), 2),
                "total_gb": round(disk.total / (1024**3), 2),
            },
            "cpu_percent": cpu,
            "load_avg": os.getloadavg() if hasattr(os, "getloadavg") else None,
        }

        if memory.percent > THRESHOLDS["memory_percent"]:
            alerts.append(f"Memory usage high: {memory.percent}%")
        if disk.percent > THRESHOLDS["disk_percent"]:
            alerts.append(f"Disk usage high: {disk.percent}%")
        if cpu > THRESHOLDS["cpu_percent"]:
            alerts.append(f"CPU usage high: {cpu}%")
    except Exception as e:
        checks["system"] = {"status": "error", "error": str(e)}

    # Overall status
    unhealthy = [k for k, v in checks.items() if v.get("status") == "unhealthy"]
    warnings = [
        k for k, v in checks.items() if v.get("status") in ("warning", "degraded")
    ]

    if unhealthy:
        overall = "unhealthy"
    elif warnings:
        overall = "degraded"
    else:
        overall = "healthy"

    return {
        "status": overall,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "version": settings.version,
        "environment": settings.environment,
        "checks": checks,
        "alerts": alerts,
        "uptime": _get_uptime(),
    }


@router.get("/metrics")
async def get_metrics(db: Session = Depends(get_db)) -> Dict[str, Any]:
    """Real-time platform metrics for monitoring dashboards."""
    now = datetime.now(timezone.utc)
    today = now.replace(hour=0, minute=0, second=0, microsecond=0)
    last_24h = now - timedelta(hours=24)
    last_7d = now - timedelta(days=7)

    # User metrics
    total_users = db.query(func.count(User.id)).scalar() or 0
    new_users_24h = (
        db.query(func.count(User.id)).filter(User.created_at >= last_24h).scalar() or 0
    )
    new_users_7d = (
        db.query(func.count(User.id)).filter(User.created_at >= last_7d).scalar() or 0
    )

    # Verification metrics
    total_verifications = db.query(func.count(Verification.id)).scalar() or 0
    verifications_24h = (
        db.query(func.count(Verification.id))
        .filter(Verification.created_at >= last_24h)
        .scalar()
        or 0
    )

    successful_24h = (
        db.query(func.count(Verification.id))
        .filter(Verification.created_at >= last_24h, Verification.status == "completed")
        .scalar()
        or 0
    )

    success_rate = (
        (successful_24h / verifications_24h * 100) if verifications_24h > 0 else 0
    )

    # Revenue metrics (last 24h)
    revenue_24h = (
        db.query(func.sum(Transaction.amount))
        .filter(
            Transaction.created_at >= last_24h,
            Transaction.status == "completed",
            Transaction.transaction_type == "credit",
        )
        .scalar()
        or 0
    )

    # Active users (users with verifications in last 24h)
    active_users = (
        db.query(func.count(func.distinct(Verification.user_id)))
        .filter(Verification.created_at >= last_24h)
        .scalar()
        or 0
    )

    # Tier distribution
    tier_counts = dict(
        db.query(User.subscription_tier, func.count(User.id))
        .group_by(User.subscription_tier)
        .all()
    )

    return {
        "timestamp": now.isoformat(),
        "users": {
            "total": total_users,
            "new_24h": new_users_24h,
            "new_7d": new_users_7d,
            "active_24h": active_users,
        },
        "verifications": {
            "total": total_verifications,
            "last_24h": verifications_24h,
            "successful_24h": successful_24h,
            "success_rate": round(success_rate, 1),
        },
        "revenue": {
            "last_24h": float(revenue_24h),
        },
        "tiers": tier_counts,
        "system": {
            "memory_percent": psutil.virtual_memory().percent,
            "cpu_percent": psutil.cpu_percent(interval=0.1),
            "disk_percent": psutil.disk_usage("/").percent,
        },
    }


@router.get("/alerts")
async def get_active_alerts(db: Session = Depends(get_db)) -> Dict[str, Any]:
    """Get all active alerts and warnings."""
    alerts = []

    # Check TextVerified balance
    try:
        from app.services.textverified_service import TextVerifiedService

        tv = TextVerifiedService()
        if tv.enabled:
            balance_data = await tv.get_balance()
            balance = (
                float(balance_data.get("balance", 0))
                if isinstance(balance_data, dict)
                else float(balance_data)
            )
            if balance <= 1.0:
                alerts.append(
                    {
                        "severity": "critical",
                        "service": "textverified",
                        "message": f"TextVerified balance critically low: ${balance:.2f}",
                        "action": "Top up immediately at textverified.com",
                    }
                )
            elif balance <= THRESHOLDS["textverified_balance"]:
                alerts.append(
                    {
                        "severity": "warning",
                        "service": "textverified",
                        "message": f"TextVerified balance low: ${balance:.2f}",
                        "action": "Consider topping up soon",
                    }
                )
    except Exception:
        pass

    # Check system resources
    memory = psutil.virtual_memory()
    if memory.percent > 90:
        alerts.append(
            {
                "severity": "critical",
                "service": "system",
                "message": f"Memory usage critical: {memory.percent}%",
                "action": "Restart services or add memory",
            }
        )
    elif memory.percent > THRESHOLDS["memory_percent"]:
        alerts.append(
            {
                "severity": "warning",
                "service": "system",
                "message": f"Memory usage high: {memory.percent}%",
                "action": "Monitor closely",
            }
        )

    disk = psutil.disk_usage("/")
    if disk.percent > THRESHOLDS["disk_percent"]:
        alerts.append(
            {
                "severity": "warning",
                "service": "system",
                "message": f"Disk usage high: {disk.percent}%",
                "action": "Clean up old logs/data",
            }
        )

    # Check Redis
    try:
        from app.core.unified_cache import cache

        if not cache.redis_client:
            alerts.append(
                {
                    "severity": "warning",
                    "service": "cache",
                    "message": "Redis unavailable, using in-memory fallback",
                    "action": "Check Redis connection settings",
                }
            )
    except Exception:
        pass

    # Check for failed payments in last hour
    last_hour = datetime.now(timezone.utc) - timedelta(hours=1)
    failed_payments = (
        db.query(func.count(PaymentLog.id))
        .filter(PaymentLog.created_at >= last_hour, PaymentLog.state == "failed")
        .scalar()
        or 0
    )

    if failed_payments > 5:
        alerts.append(
            {
                "severity": "warning",
                "service": "payments",
                "message": f"{failed_payments} failed payments in last hour",
                "action": "Check Paystack dashboard",
            }
        )

    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "alert_count": len(alerts),
        "alerts": alerts,
    }


@router.get("/services")
async def get_service_status() -> Dict[str, Any]:
    """Quick status check of all external services."""
    services = {}

    # TextVerified
    try:
        from app.services.textverified_service import TextVerifiedService

        tv = TextVerifiedService()
        services["textverified"] = {
            "enabled": tv.enabled,
            "status": "ok" if tv.enabled else "disabled",
        }
    except Exception as e:
        services["textverified"] = {
            "enabled": False,
            "status": "error",
            "error": str(e),
        }

    # Paystack
    services["paystack"] = {
        "enabled": bool(settings.paystack_secret_key),
        "status": "configured" if settings.paystack_secret_key else "not_configured",
    }

    # Email (Resend)
    services["email"] = {
        "enabled": bool(settings.resend_api_key),
        "status": "configured" if settings.resend_api_key else "not_configured",
    }

    # Redis
    try:
        from app.core.unified_cache import cache

        backend = "redis" if cache.redis_client else "memory"
        services["redis"] = {
            "enabled": cache.redis_client is not None,
            "status": "connected" if cache.redis_client else "fallback",
            "backend": backend,
        }
    except Exception:
        services["redis"] = {"enabled": False, "status": "error"}

    # Sentry
    services["sentry"] = {
        "enabled": bool(settings.sentry_dsn),
        "status": "configured" if settings.sentry_dsn else "not_configured",
    }

    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "services": services,
    }


# Startup time tracking
_startup_time = datetime.now(timezone.utc)


def _get_uptime() -> str:
    """Get human-readable uptime."""
    delta = datetime.now(timezone.utc) - _startup_time
    days = delta.days
    hours, remainder = divmod(delta.seconds, 3600)
    minutes, _ = divmod(remainder, 60)

    parts = []
    if days:
        parts.append(f"{days}d")
    if hours:
        parts.append(f"{hours}h")
    parts.append(f"{minutes}m")

    return " ".join(parts)
