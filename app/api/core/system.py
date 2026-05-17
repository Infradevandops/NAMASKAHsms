"""System API router for health checks and service status."""

import logging
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/system", tags=["System"])
root_router = APIRouter()


class ServiceStatus(BaseModel):
    service_name: str
    status: str
    success_rate: float
    last_checked: datetime


class ServiceStatusSummary(BaseModel):
    overall_status: str
    services: list
    stats: dict
    last_updated: datetime


@router.get("/health")
async def health_check(db: Session = Depends(get_db)):
    """Health check endpoint."""
    try:
        return {
            "status": "healthy",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "version": "2.4.0",
            "environment": settings.environment,
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Health check failed")


@router.get("/health/readiness")
async def readiness_check(db: Session = Depends(get_db)):
    """Kubernetes readiness probe."""
    try:
        return JSONResponse(status_code=200, content={"ready": True})
    except Exception as e:
        logger.error(f"Readiness check failed: {e}", exc_info=True)
        return JSONResponse(status_code=503, content={"ready": False})


@router.get("/health/liveness")
async def liveness_check():
    """Kubernetes liveness probe."""
    try:
        return JSONResponse(status_code=200, content={"alive": True})
    except Exception as e:
        logger.error(f"Liveness check failed: {e}", exc_info=True)
        return JSONResponse(status_code=503, content={"alive": False})


@router.get("/status", response_model=ServiceStatusSummary)
def get_service_status(db: Session = Depends(get_db)):
    """Get service status."""
    try:
        return ServiceStatusSummary(
            overall_status="operational",
            services=[],
            stats={"operational": 1, "degraded": 0, "down": 0},
            last_updated=datetime.now(timezone.utc),
        )
    except Exception as e:
        logger.error(f"Error fetching service status: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to fetch service status")


@router.get("/info")
def get_system_info():
    """Get system information."""
    try:
        return {
            "service_name": "VRENUM ACTV8TN",
            "version": "2.4.0",
            "environment": settings.environment,
        }
    except Exception as e:
        logger.error(f"Error fetching system info: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to fetch system info")


@router.get("/config")
def get_public_config():
    """Get public configuration."""
    try:
        return {
            "supported_services": ["telegram", "whatsapp", "discord"],
            "payment_methods": ["paystack"],
            "currencies": ["NGN"],
        }
    except Exception as e:
        logger.error(f"Error fetching config: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to fetch configuration")
