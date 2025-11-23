"""System API router for health checks and service status."""
from datetime import datetime, timezone
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

@root_router.get("/", response_class=HTMLResponse)
async def landing_page(request: Request):
    """Landing page."""
    return HTMLResponse(content="<h1>Namaskah SMS</h1><p>Welcome!</p>")

@root_router.get("/services", response_class=HTMLResponse)
async def services_page(request: Request):
    """Services page."""
    return HTMLResponse(content="<h1>Services</h1>")

@root_router.get("/pricing", response_class=HTMLResponse)
async def pricing_page(request: Request):
    """Pricing page."""
    return HTMLResponse(content="<h1>Pricing</h1>")

@root_router.get("/about", response_class=HTMLResponse)
async def about_page(request: Request):
    """About page."""
    return HTMLResponse(content="<h1>About</h1>")

@root_router.get("/contact", response_class=HTMLResponse)
async def contact_page(request: Request):
    """Contact page."""
    return HTMLResponse(content="<h1>Contact</h1>")

@root_router.get("/faq", response_class=HTMLResponse)
async def faq_page(request: Request):
    """FAQ page."""
    return HTMLResponse(content="<h1>FAQ</h1>")

@root_router.get("/admin", response_class=HTMLResponse)
async def admin_page(request: Request, admin_user=Depends(get_current_admin_user)):
    """Admin dashboard."""
    return HTMLResponse(content="<h1>Admin Dashboard</h1>")

@root_router.get("/status", response_class=HTMLResponse)
async def status_page(request: Request):
    """Status page."""
    return HTMLResponse(content="<h1>Status</h1>")

@root_router.get("/privacy", response_class=HTMLResponse)
async def privacy_page(request: Request):
    """Privacy page."""
    return HTMLResponse(content="<h1>Privacy</h1>")

@root_router.get("/terms", response_class=HTMLResponse)
async def terms_page(request: Request):
    """Terms page."""
    return HTMLResponse(content="<h1>Terms</h1>")

@root_router.get("/refund", response_class=HTMLResponse)
async def refund_page(request: Request):
    """Refund page."""
    return HTMLResponse(content="<h1>Refund</h1>")

@root_router.get("/cookies", response_class=HTMLResponse)
async def cookies_page(request: Request):
    """Cookies page."""
    return HTMLResponse(content="<h1>Cookies</h1>")
