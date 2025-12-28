"""
Namaskah SMS - Optimized Application Factory
"""
from fastapi import FastAPI, Request, Depends
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware as FastAPICORSMiddleware
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from starlette.middleware.gzip import GZipMiddleware
from sqlalchemy.orm import Session
from datetime import datetime
from pathlib import Path
from typing import Optional

from app.core.logging import get_logger, setup_logging
from app.core.lifespan import lifespan
from app.middleware.csrf_middleware import CSRFMiddleware
from app.middleware.xss_protection import XSSProtectionMiddleware
from app.middleware.security import SecurityHeadersMiddleware
from app.middleware.logging import RequestLoggingMiddleware
from app.core.unified_error_handling import setup_unified_middleware
from app.core.database import get_db
from app.core.config import get_settings

# Import routers
from app.api.core.auth import router as auth_router
from app.api.core.gdpr import router as gdpr_router
from app.api.core.notification_endpoints import router as notification_router
from app.api.core.dashboard_activity import router as dashboard_activity_router
from app.api.core.textverified_balance import router as textverified_balance_router
from app.api.core.user_profile import router as user_profile_router
from app.api.admin.dashboard import router as dashboard_router
from app.api.admin.verification_analytics import router as verification_analytics_router
from app.api.admin.verification_history import router as verification_history_router
from app.api.admin.user_management import router as user_management_router
from app.api.admin.audit_compliance import router as audit_compliance_router
from app.api.admin.analytics import router as analytics_router
from app.api.admin.export import router as export_router
from app.api.core.countries import router as countries_router
from app.api.core.services import router as services_router
from app.api.core.system import router as system_router
from app.api.verification.textverified_endpoints import router as textverified_router
from app.api.verification.pricing import router as pricing_router
from app.api.verification.carrier_endpoints import router as carrier_router
from app.api.verification.consolidated_verification import router as verify_router
from app.api.verification.purchase_endpoints import router as purchase_router
from app.api.billing.payment_endpoints import router as payment_router
from app.api.billing.credit_endpoints import router as credit_router
from app.api.billing.payment_history_endpoints import router as payment_history_router
from app.api.billing.pricing_endpoints import router as billing_pricing_router
from app.api.billing.refund_endpoints import router as refund_router
from app.api.billing.tier_endpoints import router as tier_router
from app.api.core.api_key_endpoints import router as api_key_router
from app.api.core.user_settings import router as user_settings_router
from app.api.core.user_settings_endpoints import router as user_settings_endpoints_router
from app.api.core.preferences import router as preferences_router
from app.api.routes_consolidated import router as routes_router
from app.api.preview_router import router as preview_router

security = HTTPBearer(auto_error=False)
TEMPLATES_DIR = Path("templates").resolve()
STATIC_DIR = Path("static").resolve()


def get_optional_user_id(credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)) -> Optional[str]:
    """Get user ID from token if provided, otherwise return None."""
    if not credentials:
        return None
    try:
        import jwt
        settings = get_settings()
        payload = jwt.decode(credentials.credentials, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
        return payload.get("user_id")
    except Exception:
        return None


def create_app() -> FastAPI:
    """Application factory pattern."""
    setup_logging()
    logger = get_logger("startup")
    settings = get_settings()

    # Initialize models
    from app.models.base import Base
    import app.models
    Base.registry.configure()

    # Create FastAPI app with lifespan
    fastapi_app = FastAPI(
        title="Namaskah SMS API",
        version="2.5.0",
        description="Modular SMS Verification Service",
        lifespan=lifespan,
    )

    # ============== MIDDLEWARE ==============
    fastapi_app.add_middleware(GZipMiddleware, minimum_size=1000)
    
    cors_origins = ["http://localhost:3000", "http://localhost:8000", "http://127.0.0.1:3000", "http://127.0.0.1:8000"]
    if settings.environment == "production":
        cors_origins = list(set([settings.base_url, settings.base_url.replace("https://", "https://app.")]))
    
    fastapi_app.add_middleware(
        FastAPICORSMiddleware,
        allow_origins=cors_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        allow_headers=["Content-Type", "Authorization", "X-CSRF-Token"],
    )
    
    setup_unified_middleware(fastapi_app)
    
    @fastapi_app.middleware("http")
    async def fix_mime_types(request: Request, call_next):
        response = await call_next(request)
        path = request.url.path
        if path.endswith('.css'):
            response.headers['content-type'] = 'text/css; charset=utf-8'
        elif path.endswith('.js'):
            response.headers['content-type'] = 'application/javascript; charset=utf-8'
        return response

    fastapi_app.add_middleware(CSRFMiddleware)
    fastapi_app.add_middleware(SecurityHeadersMiddleware)
    fastapi_app.add_middleware(XSSProtectionMiddleware)
    fastapi_app.add_middleware(RequestLoggingMiddleware)

    # ============== STATIC FILES ==============
    if STATIC_DIR.exists():
        fastapi_app.mount("/static", StaticFiles(directory=str(STATIC_DIR)))
    else:
        STATIC_DIR.mkdir(parents=True, exist_ok=True)
        fastapi_app.mount("/static", StaticFiles(directory=str(STATIC_DIR)))

    # ============== ROUTERS ==============
    # Core API
    fastapi_app.include_router(auth_router, prefix="/api")
    fastapi_app.include_router(gdpr_router, prefix="/api")
    fastapi_app.include_router(notification_router)
    fastapi_app.include_router(dashboard_activity_router)
    fastapi_app.include_router(textverified_balance_router)
    fastapi_app.include_router(user_profile_router)
    fastapi_app.include_router(countries_router, prefix="/api")
    fastapi_app.include_router(services_router)
    fastapi_app.include_router(system_router)
    
    # Admin API
    fastapi_app.include_router(dashboard_router, prefix="/api")
    fastapi_app.include_router(verification_analytics_router)
    fastapi_app.include_router(verification_history_router)
    fastapi_app.include_router(user_management_router)
    fastapi_app.include_router(audit_compliance_router)
    fastapi_app.include_router(analytics_router)
    fastapi_app.include_router(export_router)
    
    # Additional admin routers
    from app.api.admin.stats import router as stats_router
    from app.api.admin.tier_management import router as tier_management_router
    from app.api.admin.actions import router as actions_router
    from app.api.admin.pricing_control import router as pricing_control_router
    from app.api.admin.verification_actions import router as verification_actions_router
    fastapi_app.include_router(stats_router)
    fastapi_app.include_router(tier_management_router, prefix="/api")
    fastapi_app.include_router(actions_router)
    fastapi_app.include_router(pricing_control_router)
    fastapi_app.include_router(verification_actions_router)
    
    # Real-time endpoints
    from app.api.core.analytics_enhanced import router as analytics_enhanced_router
    from app.api.core.balance_sync import router as balance_sync_router
    from app.api.verification.status_polling import router as status_polling_router
    fastapi_app.include_router(analytics_enhanced_router)
    fastapi_app.include_router(balance_sync_router)
    fastapi_app.include_router(status_polling_router)
    
    # User settings
    fastapi_app.include_router(tier_router, prefix="/api")
    fastapi_app.include_router(api_key_router, prefix="/api")
    fastapi_app.include_router(user_settings_router, prefix="/api")
    fastapi_app.include_router(user_settings_endpoints_router)
    fastapi_app.include_router(preferences_router)
    
    # Verification
    fastapi_app.include_router(verify_router)
    fastapi_app.include_router(textverified_router)
    fastapi_app.include_router(pricing_router)
    fastapi_app.include_router(carrier_router)
    fastapi_app.include_router(purchase_router)
    
    # Billing
    fastapi_app.include_router(payment_router)
    fastapi_app.include_router(credit_router)
    fastapi_app.include_router(payment_history_router)
    fastapi_app.include_router(billing_pricing_router)
    fastapi_app.include_router(refund_router)
    
    # Consolidated routes (HTML pages)
    fastapi_app.include_router(routes_router)
    fastapi_app.include_router(preview_router)

    # ============== DIAGNOSTICS ==============
    templates = Jinja2Templates(directory=str(TEMPLATES_DIR))
    
    @fastapi_app.get("/api/diagnostics")
    async def diagnostics(db: Session = Depends(get_db)):
        """System diagnostics endpoint."""
        return {
            "timestamp": datetime.now().isoformat(),
            "environment": settings.environment,
            "version": "2.5.0",
            "database": {"connected": True},
            "static_files": {"mounted": STATIC_DIR.exists()},
            "templates": {"count": len(list(TEMPLATES_DIR.glob("*.html"))) if TEMPLATES_DIR.exists() else 0},
        }

    return fastapi_app


app = create_app()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
