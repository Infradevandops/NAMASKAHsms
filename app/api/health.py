"""Comprehensive health check endpoints for monitoring and observability."""

import sys
import time
from datetime import datetime, timezone
from typing import Dict, Any
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import inspect, text
from app.core.database import get_db, db_manager, test_database_connection
from app.core.cache import get_redis
from app.core.config import get_settings
from app.services.textverified_service import TextVerifiedService

router = APIRouter(tags=["health"])
settings = get_settings()


@router.get("/health")
async def health_check():
    """Basic health check endpoint."""
    return {
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "version": "4.0.0",
        "python_version": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
        "environment": settings.environment
    }


@router.get("/health/ready")
async def readiness_check():
    """Readiness check for load balancers - checks all dependencies."""
    start_time = time.time()
    checks = {}
    overall_status = "ready"
    
    # Database check
    try:
        db_status = test_database_connection()
        checks["database"] = {
            "status": "healthy" if db_status["status"] == "connected" else "unhealthy",
            "details": db_status
        }
        if db_status["status"] != "connected":
            overall_status = "not_ready"
    except Exception as e:
        checks["database"] = {"status": "unhealthy", "error": str(e)}
        overall_status = "not_ready"
    
    # Redis check
    try:
        redis = get_redis()
        redis.ping()
        checks["redis"] = {"status": "healthy"}
    except Exception as e:
        checks["redis"] = {"status": "unhealthy", "error": str(e)}
        overall_status = "not_ready"
    
    # External services check
    try:
        tv_service = TextVerifiedService()
        if tv_service.enabled:
            balance = await tv_service.get_balance()
            checks["textverified"] = {
                "status": "healthy" if "error" not in balance else "degraded",
                "balance": balance.get("balance", 0)
            }
        else:
            checks["textverified"] = {"status": "disabled"}
    except Exception as e:
        checks["textverified"] = {"status": "unhealthy", "error": str(e)}
        # Don't mark as not_ready for external service issues
    
    response_time = round((time.time() - start_time) * 1000, 2)
    
    return {
        "status": overall_status,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "response_time_ms": response_time,
        "checks": checks
    }


@router.get("/health/live")
async def liveness_check():
    """Liveness check for container orchestration - basic app responsiveness."""
    return {
        "status": "alive",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "uptime_seconds": time.time() - getattr(liveness_check, '_start_time', time.time())
    }

# Set start time for uptime calculation
liveness_check._start_time = time.time()


@router.get("/health/detailed")
async def detailed_health_check(db=Depends(get_db)):
    """Detailed health check with comprehensive system status."""
    start_time = time.time()
    
    # Database detailed check
    db_health = await _check_database_health(db)
    
    # Cache detailed check
    cache_health = await _check_cache_health()
    
    # External services check
    external_health = await _check_external_services()
    
    # System metrics
    system_metrics = _get_system_metrics()
    
    response_time = round((time.time() - start_time) * 1000, 2)
    
    # Determine overall status
    critical_issues = [
        db_health["status"] == "unhealthy",
        cache_health["status"] == "unhealthy"
    ]
    
    if any(critical_issues):
        overall_status = "unhealthy"
    elif any([
        db_health["status"] == "degraded",
        cache_health["status"] == "degraded",
        external_health["textverified"]["status"] == "degraded"
    ]):
        overall_status = "degraded"
    else:
        overall_status = "healthy"
    
    return {
        "status": overall_status,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "response_time_ms": response_time,
        "version": "4.0.0",
        "environment": settings.environment,
        "components": {
            "database": db_health,
            "cache": cache_health,
            "external_services": external_health,
            "system": system_metrics
        }
    }


async def _check_database_health(db) -> Dict[str, Any]:
    """Check database health with detailed metrics."""
    try:
        # Connection test
        start_time = time.time()
        db.execute(text("SELECT 1"))
        query_time = round((time.time() - start_time) * 1000, 2)
        
        # Schema validation
        engine = db.get_bind()
        inspector = inspect(engine)
        
        # Check critical tables exist
        tables = inspector.get_table_names()
        required_tables = ['users', 'verifications', 'transactions', 'payment_logs']
        missing_tables = [t for t in required_tables if t not in tables]
        
        # Check for critical columns
        schema_issues = []
        if 'verifications' in tables:
            columns = [col["name"] for col in inspector.get_columns("verifications")]
            if "idempotency_key" not in columns:
                schema_issues.append("Missing idempotency_key column in verifications")
        
        status = "healthy"
        if missing_tables or schema_issues:
            status = "degraded"
        
        return {
            "status": status,
            "query_time_ms": query_time,
            "circuit_breaker_failures": db_manager.circuit_breaker_failures,
            "circuit_breaker_open": db_manager.is_circuit_breaker_open(),
            "missing_tables": missing_tables,
            "schema_issues": schema_issues,
            "total_tables": len(tables)
        }
        
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
            "circuit_breaker_failures": db_manager.circuit_breaker_failures,
            "circuit_breaker_open": db_manager.is_circuit_breaker_open()
        }


async def _check_cache_health() -> Dict[str, Any]:
    """Check Redis cache health."""
    try:
        redis = get_redis()
        start_time = time.time()
        
        # Basic connectivity
        redis.ping()
        ping_time = round((time.time() - start_time) * 1000, 2)
        
        # Memory usage
        info = redis.info('memory')
        memory_used = info.get('used_memory_human', 'unknown')
        memory_peak = info.get('used_memory_peak_human', 'unknown')
        
        # Test set/get
        test_key = "health_check_test"
        redis.set(test_key, "test_value", ex=10)
        test_value = redis.get(test_key)
        redis.delete(test_key)
        
        if test_value != b"test_value":
            return {"status": "degraded", "error": "Set/get test failed"}
        
        return {
            "status": "healthy",
            "ping_time_ms": ping_time,
            "memory_used": memory_used,
            "memory_peak": memory_peak,
            "connected_clients": info.get('connected_clients', 0)
        }
        
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e)
        }


async def _check_external_services() -> Dict[str, Any]:
    """Check external service health."""
    services = {}
    
    # TextVerified API
    try:
        tv_service = TextVerifiedService()
        if tv_service.enabled:
            start_time = time.time()
            balance = await tv_service.get_balance()
            response_time = round((time.time() - start_time) * 1000, 2)
            
            if "error" in balance:
                services["textverified"] = {
                    "status": "degraded",
                    "error": balance["error"],
                    "response_time_ms": response_time
                }
            else:
                services["textverified"] = {
                    "status": "healthy",
                    "balance": balance.get("balance", 0),
                    "response_time_ms": response_time
                }
        else:
            services["textverified"] = {"status": "disabled", "reason": "Missing credentials"}
    except Exception as e:
        services["textverified"] = {"status": "unhealthy", "error": str(e)}
    
    return services


def _get_system_metrics() -> Dict[str, Any]:
    """Get basic system metrics."""
    try:
        import psutil
        
        return {
            "cpu_percent": psutil.cpu_percent(interval=0.1),
            "memory_percent": psutil.virtual_memory().percent,
            "disk_percent": psutil.disk_usage('/').percent,
            "load_average": psutil.getloadavg() if hasattr(psutil, 'getloadavg') else None
        }
    except ImportError:
        return {
            "status": "metrics_unavailable",
            "reason": "psutil not installed"
        }
    except Exception as e:
        return {
            "status": "metrics_error",
            "error": str(e)
        }
