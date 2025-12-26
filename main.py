"""
Namaskah SMS - Optimized Application Factory
"""
from app.core.logging import get_logger, setup_logging
from app.core.startup import run_startup_initialization
from app.middleware.csrf_middleware import CSRFMiddleware
from app.middleware.xss_protection import XSSProtectionMiddleware
from app.middleware.security import SecurityHeadersMiddleware
from app.middleware.logging import RequestLoggingMiddleware
from app.core.unified_error_handling import setup_unified_middleware
from fastapi import FastAPI, Request, HTTPException, Depends
from fastapi.responses import HTMLResponse, Response
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware as FastAPICORSMiddleware
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from starlette.middleware.gzip import GZipMiddleware
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional
import json
from pydantic import BaseModel

# Import essential routers only
from app.api.core.auth import router as auth_router
from app.api.core.auth_enhanced import router as auth_enhanced_router
from app.api.core.gdpr import router as gdpr_router
from app.api.admin.admin_router import router as admin_router
from app.api.admin.dashboard import router as dashboard_router
from app.api.admin.verification_analytics import router as verification_analytics_router
# from app.api.admin.pricing_templates import router as pricing_templates_router  # Disabled - file doesn't exist
from app.api.admin.verification_history import router as verification_history_router
from app.api.admin.user_management import router as user_management_router
from app.api.admin.audit_compliance import router as audit_compliance_router
from app.api.admin.analytics import router as analytics_router
from app.api.admin.export import router as export_router
from app.api.core.countries import router as countries_router
from app.api.core.services import router as services_router
from app.api.core.system import router as system_router

# Import production implementation routers
from app.api.verification.textverified_endpoints import router as textverified_router

from app.api.verification.pricing import router as pricing_router
from app.api.verification.carrier_endpoints import router as carrier_router
from app.api.verification.consolidated_verification import router as verify_router

from app.api.admin.dashboard import router as dashboard_router
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

from app.core.unified_cache import cache
from app.core.database import engine, get_db
from app.core.dependencies import get_current_user_id
from app.core.config import get_settings

security = HTTPBearer(auto_error=False)

TEMPLATES_DIR = Path("templates").resolve()
STATIC_DIR = Path("static").resolve()


def get_optional_user_id(credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)) -> Optional[str]:
    """Get user ID from token if provided, otherwise return None."""
    if not credentials:
        return None
    try:
        import jwt
        from app.core.config import get_settings
        settings = get_settings()
        payload = jwt.decode(credentials.credentials, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
        return payload.get("user_id")
    except Exception:
        return None


def create_app() -> FastAPI:
    """Application factory pattern - optimized for performance"""
    setup_logging()
    logger = get_logger("startup")

    from app.models.base import Base
    import app.models
    Base.registry.configure()

    fastapi_app = FastAPI(
        title="Namaskah SMS API",
        version="2.5.0",
        description="Modular SMS Verification Service",
    )

    try:
        run_startup_initialization()
    except Exception as e:
        logger.error(f"Startup initialization failed: {e}")
        logger.info("Continuing with partial initialization...")

    fastapi_app.add_middleware(GZipMiddleware, minimum_size=1000)

    settings = get_settings()
    cors_origins = [
        "http://localhost:3000",
        "http://localhost:8000",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:8000",
    ]
    if settings.environment == "production":
        # Production CORS - allow the actual domain
        base_url = settings.base_url
        cors_origins = [
            base_url,
            base_url.replace("https://", "https://app."),
            base_url.replace("http://", "http://app."),
        ]
        # Remove duplicates
        cors_origins = list(set(cors_origins))
    fastapi_app.add_middleware(
        FastAPICORSMiddleware,
        allow_origins=cors_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        allow_headers=["Content-Type", "Authorization", "X-CSRF-Token"],
    )

    setup_unified_middleware(fastapi_app)
    
    # Add MIME type correction middleware - MUST be after setup_unified_middleware
    @fastapi_app.middleware("http")
    async def fix_mime_types(request: Request, call_next):
        response = await call_next(request)
        path = request.url.path
        if path.endswith('.css'):
            response.headers['content-type'] = 'text/css; charset=utf-8'
        elif path.endswith('.js'):
            response.headers['content-type'] = 'application/javascript; charset=utf-8'
        elif path.endswith('.woff') or path.endswith('.woff2'):
            response.headers['content-type'] = 'font/woff2'
        elif path.endswith('.ttf'):
            response.headers['content-type'] = 'font/ttf'
        return response

    fastapi_app.add_middleware(CSRFMiddleware)
    fastapi_app.add_middleware(SecurityHeadersMiddleware)
    fastapi_app.add_middleware(XSSProtectionMiddleware)
    fastapi_app.add_middleware(RequestLoggingMiddleware)

    # Mount static files FIRST (before routes)
    if STATIC_DIR.exists():
        fastapi_app.mount("/static", StaticFiles(directory=str(STATIC_DIR)))
    else:
        logger = get_logger("startup")
        logger.error(f"Static directory '{STATIC_DIR}' not found")
        # Create a dummy static directory to prevent errors
        STATIC_DIR.mkdir(parents=True, exist_ok=True)
        fastapi_app.mount("/static", StaticFiles(directory=str(STATIC_DIR)))

    # Root router removed to prevent conflicts
    fastapi_app.include_router(auth_router, prefix="/api")
    # Skip auth_enhanced_router as it conflicts with main.py auth endpoints
    # fastapi_app.include_router(auth_enhanced_router, prefix="/api")
    fastapi_app.include_router(gdpr_router, prefix="/api")
    # Skip admin_router to avoid conflicts with new enhanced stats router
    # fastapi_app.include_router(admin_router, prefix="/api")
    fastapi_app.include_router(dashboard_router, prefix="/api")
    fastapi_app.include_router(verification_analytics_router)
    # fastapi_app.include_router(pricing_templates_router)  # Disabled - file doesn't exist
    fastapi_app.include_router(verification_history_router)
    fastapi_app.include_router(user_management_router)
    fastapi_app.include_router(audit_compliance_router)
    # Include admin routers
    from app.api.admin.stats import router as stats_router
    from app.api.admin.tier_management import router as tier_management_router
    # from app.api.admin.pricing_api import router as pricing_api_router  # Disabled - doesn't exist
    from app.api.admin.actions import router as actions_router
    from app.api.admin.pricing_control import router as pricing_control_router
    from app.api.admin.verification_actions import router as verification_actions_router
    fastapi_app.include_router(stats_router)
    fastapi_app.include_router(tier_management_router, prefix="/api")
    fastapi_app.include_router(analytics_router)
    fastapi_app.include_router(export_router)
    fastapi_app.include_router(verification_history_router)
    
    # Include real-time dashboard endpoints
    from app.api.core.analytics_enhanced import router as analytics_enhanced_router
    from app.api.core.balance_sync import router as balance_sync_router
    from app.api.verification.status_polling import router as status_polling_router
    fastapi_app.include_router(analytics_enhanced_router)
    fastapi_app.include_router(balance_sync_router)
    fastapi_app.include_router(status_polling_router)
    # fastapi_app.include_router(pricing_api_router)  # Disabled
    fastapi_app.include_router(actions_router)
    fastapi_app.include_router(pricing_control_router)
    fastapi_app.include_router(verification_actions_router)
    fastapi_app.include_router(countries_router, prefix="/api")
    fastapi_app.include_router(dashboard_router, prefix="/api")
    fastapi_app.include_router(tier_router, prefix="/api")
    fastapi_app.include_router(api_key_router, prefix="/api")
    fastapi_app.include_router(user_settings_router, prefix="/api")
    fastapi_app.include_router(user_settings_endpoints_router)
    fastapi_app.include_router(preferences_router)
    fastapi_app.include_router(verify_router, prefix="/api")
    fastapi_app.include_router(services_router)
    fastapi_app.include_router(system_router)
    fastapi_app.include_router(textverified_router, prefix="/api")  # Fix: Add TextVerified router for balance endpoint

    # fastapi_app.include_router(rentals_endpoints_router)
    fastapi_app.include_router(pricing_router)
    fastapi_app.include_router(carrier_router)
    fastapi_app.include_router(purchase_router)
    fastapi_app.include_router(payment_router)
    fastapi_app.include_router(credit_router)
    fastapi_app.include_router(payment_history_router)
    fastapi_app.include_router(billing_pricing_router)
    fastapi_app.include_router(refund_router)
    fastapi_app.include_router(routes_router)
    fastapi_app.include_router(preview_router)

    # Initialize Jinja2 templates
    templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

        # Routes consolidated in app/api/routes_consolidated.py

        # Countries and services are fetched from TextVerified API via routers

    @fastapi_app.on_event("startup")
    async def startup_event():
        startup_logger = get_logger("startup")
        startup_logger.info("Application startup - Phase 1 Task 1.1 Fix")
        
        try:
            # Connect to cache (with fallback to in-memory)
            startup_logger.info("Connecting to cache...")
            await cache.connect()
            startup_logger.info("Cache connected successfully")
        except Exception as e:
            startup_logger.error(f"Cache connection error: {e}")
            startup_logger.warning("Continuing with in-memory cache fallback")
        
        try:
            # Initialize database
            startup_logger.info("Initializing database...")
            from app.models.base import Base
            import app.models
            Base.registry.configure()
            Base.metadata.create_all(bind=engine)
            startup_logger.info("Database tables created successfully")
        except Exception as e:
            startup_logger.error(f"Database initialization error: {e}")
            raise
        
        try:
            # Create admin user if needed
            startup_logger.info("Checking admin user...")
            run_startup_initialization()
            startup_logger.info("Admin user verified")
        except Exception as e:
            startup_logger.error(f"Admin user initialization error: {e}")
        
        # Start SMS polling service
        from app.services.sms_polling_service import sms_polling_service
        from app.services.voice_polling_service import voice_polling_service
        import asyncio

        async def _run_sms_service_supervisor():
            sms_logger = get_logger("sms-supervisor")
            while True:
                try:
                    await asyncio.wait_for(
                        sms_polling_service.start_background_service(),
                        timeout=settings.async_task_timeout_seconds,
                    )
                    sms_logger.info("SMS polling service exited; restarting supervisor in 5s")
                    await asyncio.sleep(5)
                except asyncio.TimeoutError:
                    sms_logger.warning("SMS polling service timed out; restarting")
                    await asyncio.sleep(2)
                except asyncio.CancelledError:
                    sms_logger.info("SMS supervisor cancelled")
                    break
                except Exception as e:
                    sms_logger.error(f"SMS supervisor error: {e}")
                    await asyncio.sleep(5)
        
        async def _run_voice_service_supervisor():
            voice_logger = get_logger("voice-supervisor")
            while True:
                try:
                    await asyncio.wait_for(
                        voice_polling_service.start_background_service(),
                        timeout=settings.async_task_timeout_seconds,
                    )
                    voice_logger.info("Voice polling service exited; restarting supervisor in 5s")
                    await asyncio.sleep(5)
                except asyncio.TimeoutError:
                    voice_logger.warning("Voice polling service timed out; restarting")
                    await asyncio.sleep(2)
                except asyncio.CancelledError:
                    voice_logger.info("Voice supervisor cancelled")
                    break
                except Exception as e:
                    voice_logger.error(f"Voice supervisor error: {e}")
                    await asyncio.sleep(5)

        asyncio.create_task(_run_sms_service_supervisor())
        asyncio.create_task(_run_voice_service_supervisor())
        startup_logger.info("Application startup completed successfully")

    @fastapi_app.on_event("shutdown")
    async def shutdown_event():
        shutdown_logger = get_logger("shutdown")
        shutdown_logger.info("Starting graceful shutdown")
        try:
            from app.services.sms_polling_service import sms_polling_service
            from app.services.voice_polling_service import voice_polling_service
            await sms_polling_service.stop_background_service()
            await voice_polling_service.stop_background_service()
            shutdown_logger.info("Polling services stopped")
            await cache.disconnect()
            shutdown_logger.info("Cache disconnected")
            engine.dispose()
            shutdown_logger.info("Database connections disposed")
            shutdown_logger.info("Graceful shutdown completed")
        except Exception as e:
            shutdown_logger.error("Error during shutdown", error=str(e))

    # Add comprehensive diagnostics endpoint
    @fastapi_app.get("/api/diagnostics")
    async def diagnostics(db: Session = Depends(get_db)):
        """Comprehensive system diagnostics for debugging production issues."""
        from app.core.config import get_settings
        settings = get_settings()
        
        diagnostics_data = {
            "timestamp": datetime.now().isoformat(),
            "environment": settings.environment,
            "version": "2.5.0",
            "debug": settings.debug,
            "base_url": settings.base_url,
            "database": {
                "connected": False,
                "type": "unknown",
                "error": None
            },
            "static_files": {
                "mounted": STATIC_DIR.exists(),
                "path": str(STATIC_DIR)
            },
            "templates": {
                "mounted": TEMPLATES_DIR.exists(),
                "path": str(TEMPLATES_DIR),
                "count": len(list(TEMPLATES_DIR.glob("*.html"))) if TEMPLATES_DIR.exists() else 0
            },
            "cors": {
                "origins": cors_origins
            },
            "routes": {
                "total": len(fastapi_app.routes),
                "sample": [str(r.path) for r in list(fastapi_app.routes)[:5]]
            }
        }
        
        # Check database
        try:
            from sqlalchemy import text
            db.execute(text("SELECT 1"))
            diagnostics_data["database"]["connected"] = True
            diagnostics_data["database"]["type"] = "postgresql" if "postgresql" in settings.database_url else "sqlite"
        except Exception as e:
            diagnostics_data["database"]["error"] = str(e)
        
        return diagnostics_data

    return fastapi_app


app = create_app()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
