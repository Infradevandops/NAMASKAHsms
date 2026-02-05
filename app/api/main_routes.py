"""Consolidated routing - all pages and redirects."""

from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.dependencies import get_current_user_id
from app.core.logging import get_logger
from app.models.user import User

logger = get_logger(__name__)
router = APIRouter(tags=["Pages"])

# Templates directory
TEMPLATES_DIR = Path("templates").resolve()
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))


@router.get("/", response_class=HTMLResponse)
async def home_page(request: Request, db: Session = Depends(get_db)):
    """Home page - landing page for visitors."""
    # Get services data for the landing page
    from app.models.user import User

    # Get user count for social proof
    user_count = db.query(User).count()

    # Get services list (you can customize this based on your needs)
    services = [
        {"name": "Google", "id": "google"},
        {"name": "Facebook", "id": "facebook"},
        {"name": "WhatsApp", "id": "whatsapp"},
        {"name": "Instagram", "id": "instagram"},
        {"name": "Twitter", "id": "twitter"},
        {"name": "Telegram", "id": "telegram"},
        {"name": "Discord", "id": "discord"},
        {"name": "TikTok", "id": "tiktok"},
    ]

    return templates.TemplateResponse(
        "landing.html",
        {
            "request": request,
            "services": services,
            "user_count": user_count if user_count > 0 else 10000,
        },
    )


@router.get("/dashboard", response_class=HTMLResponse)
async def dashboard_page(request: Request, user_id: str = Depends(get_current_user_id), db: Session = Depends(get_db)):
    """Dashboard page."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return templates.TemplateResponse("dashboard.html", {"request": request, "user": user})


@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    """Login page."""
    return templates.TemplateResponse("login.html", {"request": request})


@router.get("/register", response_class=HTMLResponse)
async def register_page(request: Request):
    """Register page."""
    return templates.TemplateResponse("register.html", {"request": request})


@router.get("/pricing", response_class=HTMLResponse)
async def pricing_page(request: Request):
    """Pricing page."""
    return templates.TemplateResponse("pricing.html", {"request": request})


@router.get("/docs", response_class=HTMLResponse)
async def docs_page(request: Request):
    """Documentation page."""
    return templates.TemplateResponse("docs.html", {"request": request})


@router.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "namaskah-sms"}


# Redirects for common paths
@router.get("/app")
async def app_redirect():
    """Redirect /app to /dashboard."""
    return RedirectResponse(url="/dashboard", status_code=302)


@router.get("/signin")
async def signin_redirect():
    """Redirect /signin to /login."""
    return RedirectResponse(url="/login", status_code=302)


@router.get("/auth/login")
async def auth_login_redirect():
    """Redirect /auth/login to /login for compatibility."""
    return RedirectResponse(url="/login", status_code=301)


@router.get("/auth/register")
async def auth_register_redirect():
    """Redirect /auth/register to /register for compatibility."""
    return RedirectResponse(url="/register", status_code=301)


@router.get("/signup")
async def signup_redirect():
    """Redirect /signup to /register."""
    return RedirectResponse(url="/register", status_code=302)