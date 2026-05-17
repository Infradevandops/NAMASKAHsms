"""Consolidated routing - all pages and redirects."""

import logging
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import FileResponse, HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user_id
from app.core.logging import get_logger
from app.models.user import User
from app.utils.i18n import get_translations_for_template

logger = get_logger(__name__)
router = APIRouter(tags=["Pages"])

# Templates directory
TEMPLATES_DIR = Path("templates").resolve()
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))


@router.get("/favicon.ico", include_in_schema=False)
async def favicon():
    return FileResponse("static/favicon.ico")


@router.get("/", response_class=HTMLResponse)
@router.head("/")
async def home_page(request: Request):
    """Home page - landing page for visitors."""
    try:
        # Get services list
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
                "user_count": 10000,  # Static count for now
            },
        )
    except Exception as e:
        logger.error(f"Error rendering home page: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to load home page")


@router.get("/dashboard", response_class=HTMLResponse)
async def dashboard_page(
    request: Request,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Dashboard page."""
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        # Get user's preferred language (default to English)
        user_locale = getattr(user, "language", "en") or "en"

        # Load translations for embedding
        translations_json = get_translations_for_template(user_locale)

        return templates.TemplateResponse(
            "dashboard.html",
            {
                "request": request,
                "user": user,
                "translations": translations_json,
                "locale": user_locale,
            },
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"Error rendering dashboard for user {user_id}: {e}", exc_info=True
        )
        raise HTTPException(status_code=500, detail="Failed to load dashboard")


@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    """Login page."""
    try:
        return templates.TemplateResponse("login.html", {"request": request})
    except Exception as e:
        logger.error(f"Error rendering login page: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to load login page")


@router.get("/register", response_class=HTMLResponse)
async def register_page(request: Request):
    """Register page."""
    try:
        return templates.TemplateResponse("register.html", {"request": request})
    except Exception as e:
        logger.error(f"Error rendering register page: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to load register page")


@router.get("/pricing", response_class=HTMLResponse)
async def pricing_page(request: Request):
    """Pricing page."""
    try:
        return templates.TemplateResponse("pricing.html", {"request": request})
    except Exception as e:
        logger.error(f"Error rendering pricing page: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to load pricing page")


@router.get("/docs", response_class=HTMLResponse)
async def docs_page(request: Request):
    """Documentation page."""
    try:
        return templates.TemplateResponse("docs.html", {"request": request})
    except Exception as e:
        logger.error(f"Error rendering docs page: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to load documentation")


@router.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "vrenum-sms"}


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
async def auth_login_redirect(request: Request):
    """Redirect /auth/login to /login for compatibility (preserving query params)."""
    query = str(request.query_params)
    url = f"/login?{query}" if query else "/login"
    return RedirectResponse(url=url, status_code=302)


@router.get("/auth/register")
async def auth_register_redirect():
    """Redirect /auth/register to /register for compatibility."""
    return RedirectResponse(url="/register", status_code=301)


@router.get("/signup")
async def signup_redirect():
    """Redirect /signup to /register."""
    return RedirectResponse(url="/register", status_code=302)


# ============================================
# DASHBOARD PAGES (Phase 1 Implementation)
# ============================================


@router.get("/verify", response_class=HTMLResponse)
async def verify_page(
    request: Request,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """SMS Verification page."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return templates.TemplateResponse(
        "verify_modern.html", {"request": request, "user": user}
    )


@router.get("/wallet", response_class=HTMLResponse)
async def wallet_page(
    request: Request,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Wallet & Payments page."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return templates.TemplateResponse("wallet.html", {"request": request, "user": user})


@router.get("/history", response_class=HTMLResponse)
async def history_page(
    request: Request,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Verification History page."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return templates.TemplateResponse(
        "history.html", {"request": request, "user": user}
    )


@router.get("/analytics", response_class=HTMLResponse)
async def analytics_page(
    request: Request,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Analytics & Usage page."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return templates.TemplateResponse(
        "analytics.html", {"request": request, "user": user}
    )


@router.get("/notifications", response_class=HTMLResponse)
async def notifications_page(
    request: Request,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Notifications page."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return templates.TemplateResponse(
        "notifications.html", {"request": request, "user": user}
    )


@router.get("/settings", response_class=HTMLResponse)
async def settings_page(
    request: Request,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Settings page."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return templates.TemplateResponse(
        "settings.html", {"request": request, "user": user}
    )


# ============================================
# TIER-GATED PAGES (Premium Features)
# ============================================


@router.get("/webhooks", response_class=HTMLResponse)
async def webhooks_page(
    request: Request,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Webhooks page (PAYG+ only)."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return templates.TemplateResponse(
        "webhooks.html", {"request": request, "user": user}
    )


@router.get("/api-docs", response_class=HTMLResponse)
async def api_docs_page(
    request: Request,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """API Documentation page (PAYG+ only)."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return templates.TemplateResponse(
        "api_docs.html", {"request": request, "user": user}
    )


@router.get("/referrals", response_class=HTMLResponse)
async def referrals_page(
    request: Request,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Referral Program page (PAYG+ only)."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return templates.TemplateResponse(
        "referrals.html", {"request": request, "user": user}
    )


@router.get("/voice-verify", response_class=HTMLResponse)
async def voice_verify_page(
    request: Request,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Voice Verification page (PAYG+ only)."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return templates.TemplateResponse(
        "voice_verify_modern.html", {"request": request, "user": user}
    )


@router.get("/rentals", response_class=HTMLResponse)
async def rentals_page(
    request: Request,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Number Rentals page - Rent dedicated numbers for long-term use."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return templates.TemplateResponse(
        "rentals_modern.html", {"request": request, "user": user}
    )


@router.get("/whitelabel", response_class=HTMLResponse)
async def whitelabel_page(
    request: Request,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Whitelabel setup page (Pro+ only)."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return templates.TemplateResponse(
        "whitelabel_setup.html", {"request": request, "user": user}
    )


@router.get("/email-templates", response_class=HTMLResponse)
async def email_templates_page(
    request: Request,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Email Templates editor page (Pro+ only)."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return templates.TemplateResponse(
        "email_templates.html", {"request": request, "user": user}
    )


@router.get("/telegram", response_class=HTMLResponse)
async def telegram_settings_page(
    request: Request,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Telegram integration settings page."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return templates.TemplateResponse(
        "telegram_settings.html", {"request": request, "user": user}
    )


@router.get("/push-settings", response_class=HTMLResponse)
async def push_settings_page(
    request: Request,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Push notification settings page."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return templates.TemplateResponse(
        "push_settings.html", {"request": request, "user": user}
    )


# ============================================
# ADDITIONAL PAGES
# ============================================


@router.get("/admin", response_class=HTMLResponse)
async def admin_page(
    request: Request,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Admin Dashboard page (Admin only)."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if not user.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")
    return templates.TemplateResponse(
        "admin/dashboard.html", {"request": request, "user": user}
    )


@router.get("/admin/rentals", response_class=HTMLResponse)
async def admin_rentals_page(
    request: Request,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user or not user.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")
    return templates.TemplateResponse(
        "admin/rentals.html", {"request": request, "user": user}
    )


@router.get("/admin/tier-management", response_class=HTMLResponse)
async def admin_tier_management_page(
    request: Request,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user or not user.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")
    return templates.TemplateResponse(
        "admin/tier_management.html", {"request": request, "user": user}
    )


@router.get("/admin/pricing-templates", response_class=HTMLResponse)
async def admin_pricing_templates_page(
    request: Request,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user or not user.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")
    return templates.TemplateResponse(
        "admin/pricing_templates.html", {"request": request, "user": user}
    )


@router.get("/admin/verification-history", response_class=HTMLResponse)
async def admin_verification_history_page(
    request: Request,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user or not user.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")
    return templates.TemplateResponse(
        "admin/verification_history.html", {"request": request, "user": user}
    )


@router.get("/admin/logging", response_class=HTMLResponse)
async def admin_logging_page(
    request: Request,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user or not user.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")
    return templates.TemplateResponse(
        "admin/logging_dashboard.html", {"request": request, "user": user}
    )


@router.get("/admin/user-management", response_class=HTMLResponse)
async def admin_user_management_page(
    request: Request,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Admin User Management page."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user or not user.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")
    return templates.TemplateResponse(
        "admin/user_management.html", {"request": request, "user": user}
    )


@router.get("/admin/support-tickets", response_class=HTMLResponse)
async def admin_support_tickets_page(
    request: Request,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Admin Support Tickets page."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user or not user.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")
    return templates.TemplateResponse(
        "admin/support_tickets.html", {"request": request, "user": user}
    )


@router.get("/admin/kyc-management", response_class=HTMLResponse)
async def admin_kyc_management_page(
    request: Request,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Admin KYC Management page."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user or not user.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")
    return templates.TemplateResponse(
        "admin/kyc_management.html", {"request": request, "user": user}
    )


@router.get("/admin/compliance", response_class=HTMLResponse)
async def admin_compliance_page(
    request: Request,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Admin Compliance Dashboard page."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user or not user.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")
    return templates.TemplateResponse(
        "admin/compliance.html", {"request": request, "user": user}
    )


@router.get("/admin/refund-monitoring", response_class=HTMLResponse)
async def admin_refund_monitoring_page(
    request: Request,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Admin Refund Monitoring page."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user or not user.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")
    return templates.TemplateResponse(
        "admin/refund_monitoring.html", {"request": request, "user": user}
    )


@router.get("/admin/verification-actions", response_class=HTMLResponse)
async def admin_verification_actions_page(
    request: Request,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Admin Verification Actions page."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user or not user.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")
    return templates.TemplateResponse(
        "admin/verification_actions.html", {"request": request, "user": user}
    )


@router.get("/admin/actions", response_class=HTMLResponse)
async def admin_actions_page(
    request: Request,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Admin Actions page."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user or not user.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")
    return templates.TemplateResponse(
        "admin/admin_actions.html", {"request": request, "user": user}
    )


@router.get("/disputes", response_class=HTMLResponse)
async def disputes_page(
    request: Request,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """User Disputes page."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return templates.TemplateResponse(
        "disputes.html", {"request": request, "user": user}
    )


@router.get("/admin/analytics-advanced", response_class=HTMLResponse)
async def admin_analytics_advanced_page(
    request: Request,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Admin Advanced Analytics page."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user or not user.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")
    return templates.TemplateResponse(
        "admin/analytics_advanced.html", {"request": request, "user": user}
    )


@router.get("/admin/area-code-analytics", response_class=HTMLResponse)
async def admin_area_code_analytics_page(
    request: Request,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Admin Area Code Analytics page."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user or not user.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")
    return templates.TemplateResponse(
        "admin/area_code_analytics.html", {"request": request, "user": user}
    )


@router.get("/admin/export", response_class=HTMLResponse)
async def admin_export_page(
    request: Request,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Admin Export page."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user or not user.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")
    return templates.TemplateResponse(
        "admin/export.html", {"request": request, "user": user}
    )


@router.get("/profile", response_class=HTMLResponse)
async def profile_page(
    request: Request,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """User profile page."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return templates.TemplateResponse(
        "profile.html", {"request": request, "user": user}
    )


@router.get("/privacy-settings", response_class=HTMLResponse)
async def privacy_settings_page(request: Request):
    return templates.TemplateResponse("gdpr_settings.html", {"request": request})


@router.get("/about", response_class=HTMLResponse)
async def about_page(request: Request):
    return templates.TemplateResponse("about.html", {"request": request})


@router.get("/contact", response_class=HTMLResponse)
async def contact_page(request: Request):
    return templates.TemplateResponse("contact.html", {"request": request})


@router.get("/faq", response_class=HTMLResponse)
async def faq_page(request: Request):
    return templates.TemplateResponse("faq.html", {"request": request})


@router.get("/affiliate", response_class=HTMLResponse)
async def affiliate_page(request: Request):
    return templates.TemplateResponse("affiliate_program.html", {"request": request})


@router.get("/status", response_class=HTMLResponse)
async def status_page(request: Request):
    return templates.TemplateResponse("status.html", {"request": request})


@router.get("/password-reset", response_class=HTMLResponse)
async def password_reset_page(request: Request):
    return templates.TemplateResponse("password_reset.html", {"request": request})


@router.get("/api-keys", response_class=HTMLResponse)
async def api_keys_page(
    request: Request,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return templates.TemplateResponse(
        "api_keys.html", {"request": request, "user": user}
    )


@router.get("/support")
async def support_redirect():
    return RedirectResponse(url="/contact", status_code=302)


@router.get("/landing")
async def landing_redirect():
    return RedirectResponse(url="/", status_code=302)


@router.get("/gdpr")
async def gdpr_redirect():
    return RedirectResponse(url="/privacy-settings", status_code=302)


@router.get("/auth/forgot-password")
async def forgot_password_redirect():
    return RedirectResponse(url="/password-reset", status_code=302)


@router.get("/waitlist", response_class=HTMLResponse)
async def waitlist_page(request: Request):
    """Waitlist signup page."""
    return templates.TemplateResponse("waitlist.html", {"request": request})


@router.get("/billing-history", response_class=HTMLResponse)
async def billing_history_page(
    request: Request,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Billing History page."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return templates.TemplateResponse(
        "billing_history.html", {"request": request, "user": user}
    )


@router.get("/usage-quotas", response_class=HTMLResponse)
async def usage_quotas_page(
    request: Request,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Usage Quotas page."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return templates.TemplateResponse(
        "usage_quotas.html", {"request": request, "user": user}
    )


@router.get("/insights", response_class=HTMLResponse)
async def insights_page(
    request: Request,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """User Insights Dashboard."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return templates.TemplateResponse(
        "insights.html", {"request": request, "user": user}
    )


@router.get("/support-center", response_class=HTMLResponse)
async def support_center_page(
    request: Request,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Support Center - User ticket submission."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return templates.TemplateResponse(
        "support.html", {"request": request, "user": user}
    )


@router.get("/api-documentation", response_class=HTMLResponse)
async def api_documentation_page(
    request: Request,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """API Documentation page (Pro+ only)."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return templates.TemplateResponse(
        "api_documentation.html", {"request": request, "user": user}
    )


@router.get("/webhooks-management", response_class=HTMLResponse)
async def webhooks_management_page(
    request: Request,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Webhooks Management page (PAYG+ only)."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return templates.TemplateResponse(
        "webhooks_management.html", {"request": request, "user": user}
    )


@router.get("/admin/disaster-recovery", response_class=HTMLResponse)
async def admin_disaster_recovery_page(
    request: Request,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Admin Disaster Recovery page."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user or not user.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")
    return templates.TemplateResponse(
        "admin/disaster_recovery.html", {"request": request, "user": user}
    )


@router.get("/admin/alerts", response_class=HTMLResponse)
async def admin_alerts_page(
    request: Request,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Admin Alerts & Monitoring page."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user or not user.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")
    return templates.TemplateResponse(
        "admin/alerts.html", {"request": request, "user": user}
    )
