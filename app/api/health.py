"""Health check endpoint for monitoring and deployment verification."""

import sys
from datetime import datetime

from fastapi import APIRouter

router = APIRouter(tags=["health"])


@router.get("/health")
async def health_check():
    """Basic health check endpoint."""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "4.0.0",
        "python_version": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
    }


@router.get("/health/ready")
async def readiness_check():
    """Readiness check for load balancers."""
    return {"status": "ready"}


@router.get("/health/live")
async def liveness_check():
    """Liveness check for container orchestration."""
    return {"status": "alive"}
