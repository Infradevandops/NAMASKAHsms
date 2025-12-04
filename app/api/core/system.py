"""System API router for health checks and service status."""
from datetime import datetime, timezone
from pathlib import Path
from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.core.database import get_db
from app.core.dependencies import get_current_admin_user
from app.core.config import settings

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

def check_system_health(db):
    return {"database": "connected"}

def check_database_health(db):
    return {"status": "healthy"}

@router.get("/health")
async def health_check(db: Session = Depends(get_db)):
    """Health check endpoint."""
    return {
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "version": "2.4.0",
        "environment": settings.environment,
    }

@router.get("/health/readiness")
async def readiness_check(db: Session = Depends(get_db)):
    """Kubernetes readiness probe."""
    return JSONResponse(status_code=200, content={"ready": True})

@router.get("/health/liveness")
async def liveness_check():
    """Kubernetes liveness probe."""
    return JSONResponse(status_code=200, content={"alive": True})

@router.get("/status", response_model=ServiceStatusSummary)
def get_service_status(db: Session = Depends(get_db)):
    """Get service status."""
    return ServiceStatusSummary(
        overall_status="operational",
        services=[],
        stats={"operational": 1, "degraded": 0, "down": 0},
        last_updated=datetime.now(timezone.utc),
    )

@router.get("/info")
def get_system_info():
    """Get system information."""
    return {
        "service_name": "Namaskah SMS",
        "version": "2.4.0",
        "environment": settings.environment,
    }

@router.get("/config")
def get_public_config():
    """Get public configuration."""
    return {
        "supported_services": ["telegram", "whatsapp", "discord"],
        "payment_methods": ["paystack"],
        "currencies": ["NGN"],
    }


