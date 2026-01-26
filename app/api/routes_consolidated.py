"""Consolidated routing - all pages and redirects."""

from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import (
    get_current_user_id,
    get_optional_user_id,
    require_tier,
)
from app.core.logging import get_logger

logger = get_logger(__name__)
TEMPLATES_DIR = Path("templates").resolve()
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

router = APIRouter()

# Tier dependencies for page routes
require_payg = require_tier("payg")
require_pro = require_tier("pro")

# ============================================================================
# PUBLIC PAGES
# ============================================================================

# DISABLED: Welcome page - will be re-enabled with full i18n implementation
# See docs/I18N_IMPLEMENTATION.md for roadmap
# @router.get("/welcome", response_class=HTMLResponse)
# async def welcome_page(request: Request):
#     """Language & currency selector."""
#     return templates.TemplateResponse("welcome.html", {"request": request})


@router.get("/landing", response_class=HTMLResponse)
async def landing_page(request: Request, db: Session = Depends(get_db)):
    """Landing page with pricing tiers."""
    try:
        from app.models.user import User

        # Try to get tiers, but don't fail if table doesn't exist
        tiers = []
        user_count = 0
        try:
            from app.models.subscription_tier import SubscriptionTier

            tiers = db.query(SubscriptionTier).order_by(SubscriptionTier.price_monthly).all()
            user_count = db.query(User).count()
        except Exception as db_error:
            logger.warning(f"Database query failed, using defaults: {db_error}")

        services = [
            {"id": "telegram", "name": "Telegram", "cost": 0.50},
            {"id": "whatsapp", "name": "WhatsApp", "cost": 0.75},
            {"id": "google", "name": "Google", "cost": 0.50},
            {"id": "facebook", "name": "Facebook", "cost": 0.60},
        ]

        return templates.TemplateResponse(
            "landing.html",
            {
                "request": request,
                "tiers": tiers,
                "services": services,
                "user_count": user_count,
                "user": None,
            },
        )
    except Exception as e:
        logger.error(f"Landing page error: {e}")
        raise HTTPException(status_code=500, detail="Landing page error")


@router.get("/auth/login", response_class=HTMLResponse)
async def login_page(request: Request):
    """Login page."""
    return templates.TemplateResponse("login.html", {"request": request})


@router.get("/auth/register", response_class=HTMLResponse)
async def register_page(request: Request):
    """Register page."""
    return templates.TemplateResponse("register.html", {"request": request})


@router.get("/register", response_class=HTMLResponse)
async def register_page_alt(request: Request):
    """Register page (alt route)."""
    return templates.TemplateResponse("register.html", {"request": request})


@router.get("/pricing", response_class=HTMLResponse)
async def pricing_page(request: Request):
    """Pricing page - public, no authentication required."""
    return templates.TemplateResponse("pricing.html", {"request": request})


# ============================================================================
# AUTHENTICATED PAGES
# ============================================================================


@router.get("/dashboard", response_class=HTMLResponse)
async def dashboard_page(
    request: Request,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """User dashboard."""
    from app.models.user import User

    user = db.query(User).filter(User.id == user_id).first()
    return templates.TemplateResponse("dashboard.html", {"request": request, "user": user})


@router.get("/verify", response_class=HTMLResponse)
async def verify_page(
    request: Request,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """SMS verification page."""
    from app.models.user import User

    user = db.query(User).filter(User.id == user_id).first()
    return templates.TemplateResponse("verify.html", {"request": request, "user": user})


@router.get("/verify/modern", response_class=HTMLResponse)
async def verify_modern_page(
    request: Request,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Modern SMS verification page with improved UX."""
    from app.models.user import User

    user = db.query(User).filter(User.id == user_id).first()
    return templates.TemplateResponse("verify_modern.html", {"request": request, "user": user})


@router.get("/verify/voice", response_class=HTMLResponse)
async def voice_verify_page(
    request: Request,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Voice verification page."""
    from app.models.user import User

    user = db.query(User).filter(User.id == user_id).first()
    return templates.TemplateResponse("voice_verify.html", {"request": request, "user": user})


@router.get("/verify/voice/modern", response_class=HTMLResponse)
async def voice_verify_modern_page(
    request: Request,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Modern voice verification page with improved UX."""
    from app.models.user import User

    user = db.query(User).filter(User.id == user_id).first()
    return templates.TemplateResponse("voice_verify_modern.html", {"request": request, "user": user})


@router.get("/wallet", response_class=HTMLResponse)
async def wallet_page(
    request: Request,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Wallet/billing page."""
    from app.models.user import User

    user = db.query(User).filter(User.id == user_id).first()
    return templates.TemplateResponse("wallet.html", {"request": request, "user": user})


@router.get("/profile", response_class=HTMLResponse)
async def profile_page(
    request: Request,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """User profile page."""
    from app.models.user import User

    user = db.query(User).filter(User.id == user_id).first()
    return templates.TemplateResponse("profile.html", {"request": request, "user": user})


@router.get("/settings", response_class=HTMLResponse)
async def settings_page(
    request: Request,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Settings page."""
    from app.models.user import User

    user = db.query(User).filter(User.id == user_id).first()
    return templates.TemplateResponse("settings.html", {"request": request, "tab": "account", "user": user})


@router.get("/history", response_class=HTMLResponse)
async def history_page(
    request: Request,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Verification history page."""
    from app.models.user import User

    user = db.query(User).filter(User.id == user_id).first()
    return templates.TemplateResponse("history.html", {"request": request, "tab": "history", "user": user})


@router.get("/analytics", response_class=HTMLResponse)
async def analytics_page(
    request: Request,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Analytics dashboard page."""
    from app.models.user import User

    user = db.query(User).filter(User.id == user_id).first()
    return templates.TemplateResponse("analytics.html", {"request": request, "user": user})


@router.get("/notifications", response_class=HTMLResponse)
async def notifications_page(
    request: Request,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Notifications center page."""
    from app.models.user import User

    user = db.query(User).filter(User.id == user_id).first()
    return templates.TemplateResponse("notifications.html", {"request": request, "user": user})


@router.get("/privacy-settings", response_class=HTMLResponse)
async def privacy_settings_page(
    request: Request,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """GDPR/Privacy settings page (authenticated)."""
    from app.models.user import User

    user = db.query(User).filter(User.id == user_id).first()
    return templates.TemplateResponse("gdpr_settings.html", {"request": request, "user": user})


@router.get("/webhooks", response_class=HTMLResponse)
async def webhooks_page(
    request: Request,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Webhook builder page."""
    from app.models.user import User

    user = db.query(User).filter(User.id == user_id).first()
    return templates.TemplateResponse("webhooks.html", {"request": request, "user": user})


@router.get("/referrals", response_class=HTMLResponse)
async def referrals_page(
    request: Request,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Referral program dashboard."""
    from app.models.user import User

    user = db.query(User).filter(User.id == user_id).first()
    return templates.TemplateResponse("referrals.html", {"request": request, "user": user})


# ============================================================================
# ADMIN PAGES
# ============================================================================


@router.get("/admin", response_class=HTMLResponse)
async def admin_dashboard(
    request: Request,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Admin dashboard."""
    from app.models.user import User

    user = db.query(User).filter(User.id == user_id).first()
    if not user or not user.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")
    return templates.TemplateResponse("admin/dashboard.html", {"request": request, "user": user})


@router.get("/admin/tier-management", response_class=HTMLResponse)
async def admin_tier_management(
    request: Request,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Admin tier management."""
    from app.models.user import User

    user = db.query(User).filter(User.id == user_id).first()
    if not user or not user.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")
    return templates.TemplateResponse("admin/tier_management.html", {"request": request, "user": user})


@router.get("/admin/verification-history", response_class=HTMLResponse)
async def admin_verification_history(
    request: Request,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Admin verification history."""
    from app.models.user import User

    user = db.query(User).filter(User.id == user_id).first()
    if not user or not user.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")
    return templates.TemplateResponse("admin/verification_history.html", {"request": request, "user": user})


@router.get("/admin/pricing-templates", response_class=HTMLResponse)
async def admin_pricing_templates(
    request: Request,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Admin pricing templates."""
    from app.models.user import User

    user = db.query(User).filter(User.id == user_id).first()
    if not user or not user.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")
    return templates.TemplateResponse("admin/pricing_templates.html", {"request": request, "user": user})


@router.get("/admin/logs", response_class=HTMLResponse)
async def admin_logging_dashboard(
    request: Request,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Admin logging dashboard."""
    from app.models.user import User

    user = db.query(User).filter(User.id == user_id).first()
    if not user or not user.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")
    return templates.TemplateResponse("admin/logging_dashboard.html", {"request": request, "user": user})


# ============================================================================
# INFO PAGES
# ============================================================================


@router.get("/about", response_class=HTMLResponse)
async def about_page(request: Request):
    """About page."""
    return templates.TemplateResponse(
        "info.html",
        {"request": request, "page_type": "about", "page_title": "About Namaskah"},
    )


@router.get("/contact", response_class=HTMLResponse)
async def contact_page(request: Request):
    """Contact page."""
    return templates.TemplateResponse(
        "info.html",
        {"request": request, "page_type": "contact", "page_title": "Contact Us"},
    )


@router.get("/faq", response_class=HTMLResponse)
async def faq_page(request: Request):
    """FAQ page."""
    return templates.TemplateResponse("info.html", {"request": request, "page_type": "faq", "page_title": "FAQ"})


@router.get("/privacy", response_class=HTMLResponse)
async def privacy_page(request: Request):
    """Privacy policy page."""
    return templates.TemplateResponse(
        "info.html",
        {"request": request, "page_type": "privacy", "page_title": "Privacy Policy"},
    )


@router.get("/terms", response_class=HTMLResponse)
async def terms_page(request: Request):
    """Terms of service page."""
    return templates.TemplateResponse(
        "info.html",
        {"request": request, "page_type": "terms", "page_title": "Terms of Service"},
    )


@router.get("/refund", response_class=HTMLResponse)
async def refund_page(request: Request):
    """Refund policy page."""
    return templates.TemplateResponse(
        "info.html",
        {"request": request, "page_type": "refund", "page_title": "Refund Policy"},
    )


@router.get("/cookies", response_class=HTMLResponse)
async def cookies_page(request: Request):
    """Cookie policy page."""
    return templates.TemplateResponse(
        "info.html",
        {"request": request, "page_type": "cookies", "page_title": "Cookie Policy"},
    )


@router.get("/status", response_class=HTMLResponse)
async def status_page(
    request: Request,
    user_id: Optional[str] = Depends(get_optional_user_id),
    db: Session = Depends(get_db),
):
    """Service status page with provider health."""
    from app.models.user import User

    user = None
    if user_id:
        user = db.query(User).filter(User.id == user_id).first()
    return templates.TemplateResponse("status.html", {"request": request, "user": user})


# ============================================================================
# REDIRECTS & LEGACY ROUTES
# ============================================================================


@router.get("/", response_class=HTMLResponse)
async def home(request: Request, user_id: Optional[str] = Depends(get_optional_user_id)):
    """Home - redirect to appropriate page."""
    if user_id:
        return RedirectResponse(url="/dashboard", status_code=302)
    return RedirectResponse(url="/landing", status_code=302)


@router.get("/app", response_class=HTMLResponse)
async def app_redirect(request: Request):
    """App redirect."""
    return RedirectResponse(url="/dashboard", status_code=302)


@router.get("/admin-dashboard", response_class=HTMLResponse)
async def admin_dashboard_redirect(request: Request):
    """Admin dashboard redirect."""
    return RedirectResponse(url="/admin", status_code=302)


@router.get("/account-settings", response_class=HTMLResponse)
async def account_settings_redirect(request: Request):
    """Account settings redirect."""
    return RedirectResponse(url="/settings", status_code=302)


@router.get("/privacy-settings", response_class=HTMLResponse)
async def privacy_settings_redirect(request: Request):
    """Privacy settings redirect."""
    return RedirectResponse(url="/settings", status_code=302)


@router.get("/api-keys", response_class=HTMLResponse)
async def api_keys_redirect(request: Request):
    """API keys redirect."""
    return RedirectResponse(url="/settings", status_code=302)


@router.get("/billing", response_class=HTMLResponse)
async def billing_redirect(request: Request):
    """Billing redirect."""
    return RedirectResponse(url="/wallet", status_code=302)


@router.get("/sms-inbox", response_class=HTMLResponse)
async def sms_inbox_redirect(request: Request):
    """SMS inbox redirect."""
    return RedirectResponse(url="/verify", status_code=302)


# Note: /notifications route is now a real page, not a redirect
# See notifications_page() above


@router.get("/verification", response_class=HTMLResponse)
async def verification_redirect(request: Request):
    """Verification redirect."""
    return RedirectResponse(url="/verify", status_code=302)


@router.get("/dashboard-complete", response_class=HTMLResponse)
async def dashboard_complete_redirect(request: Request):
    """Dashboard complete redirect."""
    return RedirectResponse(url="/dashboard", status_code=302)


@router.get("/analytics-dashboard", response_class=HTMLResponse)
async def analytics_dashboard_redirect(request: Request):
    """Analytics dashboard redirect."""
    return RedirectResponse(url="/admin", status_code=302)


@router.get("/test-login", response_class=HTMLResponse)
async def test_login_page(request: Request):
    """Test login page."""
    return templates.TemplateResponse("test_login.html", {"request": request})


@router.get("/voice-verify", response_class=HTMLResponse)
async def voice_verify_page(
    request: Request,
    user_id: str = Depends(require_payg),
    db: Session = Depends(get_db),
):
    """Voice verification page. Requires payg tier or higher."""
    from app.models.user import User

    user = db.query(User).filter(User.id == user_id).first()
    return templates.TemplateResponse("voice_verify.html", {"request": request, "user": user})


@router.get("/voice-status/{verification_id}", response_class=HTMLResponse)
async def voice_status_page(
    request: Request,
    verification_id: str,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Voice status page."""
    from app.models.user import User

    user = db.query(User).filter(User.id == user_id).first()
    return templates.TemplateResponse(
        "voice_status.html",
        {"request": request, "user": user, "verification_id": verification_id},
    )


@router.get("/verification-modal", response_class=HTMLResponse)
async def verification_modal(request: Request):
    """Verification modal."""
    return templates.TemplateResponse("verification_modal.html", {"request": request})


# ============================================================================
# TIER-GATED PAGES
# ============================================================================


@router.get("/api-docs", response_class=HTMLResponse)
async def api_docs_page(
    request: Request,
    user_id: str = Depends(require_payg),
    db: Session = Depends(get_db),
):
    """API documentation page. Requires payg tier or higher."""
    from app.models.user import User

    user = db.query(User).filter(User.id == user_id).first()
    return templates.TemplateResponse("api_docs.html", {"request": request, "user": user})


@router.get("/affiliate", response_class=HTMLResponse)
async def affiliate_page(
    request: Request,
    user_id: str = Depends(require_payg),
    db: Session = Depends(get_db),
):
    """Affiliate program page. Requires payg tier or higher."""
    from app.models.user import User

    user = db.query(User).filter(User.id == user_id).first()
    return templates.TemplateResponse("affiliate_program.html", {"request": request, "user": user})


@router.get("/bulk-purchase", response_class=HTMLResponse)
async def bulk_purchase_page(request: Request, user_id: str = Depends(require_pro), db: Session = Depends(get_db)):
    """Bulk purchase page. Requires pro tier or higher."""
    from app.models.user import User

    user = db.query(User).filter(User.id == user_id).first()
    return templates.TemplateResponse("bulk_purchase.html", {"request": request, "user": user})
