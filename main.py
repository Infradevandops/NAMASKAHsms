"""
Namaskah SMS - Modular Application Factory
"""
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

# Import all routers
from app.api.admin import router as admin_router
from app.api.affiliate import router as affiliate_router
from app.api.ai_features import router as ai_router
from app.api.analytics import router as analytics_router
from app.api.analytics_dashboard import router as analytics_dashboard_router
from app.api.auth import router as auth_router
from app.api.blacklist import router as blacklist_router
from app.api.bulk_verification import router as bulk_router
from app.api.business_features import router as business_router
from app.api.compliance import router as compliance_router
from app.api.countries import router as countries_router
from app.api.dashboard import router as dashboard_router
from app.api.disaster_recovery import router as dr_router
from app.api.enterprise import router as enterprise_router
from app.api.forwarding import router as forwarding_router
from app.api.infrastructure import router as infrastructure_router
from app.api.monitoring import router as monitoring_router
from app.api.preferences import router as preferences_router
from app.api.rentals import router as rentals_router
from app.api.reseller import router as reseller_router
from app.api.revenue_sharing import router as revenue_router
from app.api.services import router as services_router
from app.api.setup import router as setup_router
from app.api.support import router as support_router
from app.api.system import root_router
from app.api.system import router as system_router
from app.api.telegram import router as telegram_router
from app.api.textverified import router as textverified_router
from app.api.verification import router as verification_router
from app.api.waitlist import router as waitlist_router
from app.api.wallet import router as wallet_router
from app.api.webhooks import router as webhooks_router
from app.api.websocket import router as websocket_router
from app.api.whatsapp import router as whatsapp_router
from app.api.whitelabel import router as whitelabel_router
from app.api.whitelabel_enhanced import router as whitelabel_enhanced_router
from app.core.caching import cache
from app.core.database import engine
from app.core.exceptions import setup_exception_handlers
from app.core.logging import get_logger, setup_logging
from app.core.security_hardening import SecurityMiddleware
from app.core.startup import run_startup_initialization
from app.middleware.error_handler import ErrorHandlingMiddleware
from app.middleware.error_handling import setup_error_handling
from app.middleware.logging import RequestLoggingMiddleware
from app.middleware.rate_limiting import RateLimitMiddleware
# Import middleware
from app.middleware.security import (CORSMiddleware, JWTAuthMiddleware,
                                     SecurityHeadersMiddleware)
from app.middleware.whitelabel import WhiteLabelMiddleware


def create_app() -> FastAPI:
    """Application factory pattern"""
    # Setup logging first - before any other operations
    setup_logging()

    # Import all models and configure registry
    import app.models  # noqa: F401
    from app.models.base import Base  # noqa: F401
    Base.registry.configure()

    fastapi_app = FastAPI(
        title="Namaskah SMS API",
        version="2.5.0",
        description="Modular SMS Verification Service",
    )

    # Run startup initialization
    try:
        run_startup_initialization()
    except Exception as e:
        logger = get_logger("startup")
        logger.error(f"Startup initialization failed: {e}")

    # Setup exception handlers
    setup_exception_handlers(fastapi_app)

    # Setup enhanced error handling
    setup_error_handling(fastapi_app)

    # Add middleware (order matters - security first, minimal stack)
    fastapi_app.add_middleware(SecurityMiddleware)
    fastapi_app.add_middleware(SecurityHeadersMiddleware)
    fastapi_app.add_middleware(CORSMiddleware)
    fastapi_app.add_middleware(JWTAuthMiddleware)
    fastapi_app.add_middleware(RateLimitMiddleware)
    fastapi_app.add_middleware(ErrorHandlingMiddleware)
    fastapi_app.add_middleware(RequestLoggingMiddleware)
    fastapi_app.add_middleware(WhiteLabelMiddleware)

    # Include all routers
    fastapi_app.include_router(root_router)
    fastapi_app.include_router(auth_router)
    fastapi_app.include_router(verification_router, prefix="/api")
    fastapi_app.include_router(bulk_router, prefix="/api")
    fastapi_app.include_router(preferences_router, prefix="/api")
    fastapi_app.include_router(blacklist_router, prefix="/api")
    fastapi_app.include_router(forwarding_router, prefix="/api")
    fastapi_app.include_router(business_router, prefix="/api")
    fastapi_app.include_router(services_router)
    fastapi_app.include_router(websocket_router)
    fastapi_app.include_router(webhooks_router)
    fastapi_app.include_router(wallet_router)
    fastapi_app.include_router(admin_router)
    fastapi_app.include_router(analytics_router)
    fastapi_app.include_router(analytics_dashboard_router, prefix="/api")
    fastapi_app.include_router(system_router)
    fastapi_app.include_router(setup_router)
    fastapi_app.include_router(countries_router, prefix="/api")
    fastapi_app.include_router(dashboard_router)
    fastapi_app.include_router(support_router)
    fastapi_app.include_router(rentals_router)
    fastapi_app.include_router(waitlist_router)
    fastapi_app.include_router(whatsapp_router)
    fastapi_app.include_router(ai_router)
    fastapi_app.include_router(telegram_router)
    fastapi_app.include_router(whitelabel_router)
    fastapi_app.include_router(enterprise_router)
    fastapi_app.include_router(infrastructure_router)
    fastapi_app.include_router(monitoring_router)
    fastapi_app.include_router(dr_router)
    fastapi_app.include_router(compliance_router)
    fastapi_app.include_router(affiliate_router)
    fastapi_app.include_router(revenue_router)
    fastapi_app.include_router(whitelabel_enhanced_router)
    fastapi_app.include_router(reseller_router)
    fastapi_app.include_router(textverified_router)

    # Static files
    fastapi_app.mount("/static", StaticFiles(directory="static"), name="static")

    # Cache template content
    _template_cache = {}

    def _load_template(path: str) -> str:
        if path not in _template_cache:
            try:
                with open(f"templates/{path}", "r") as f:
                    _template_cache[path] = f.read()
            except Exception:
                _template_cache[path] = "<h1>Page not found</h1>"
        return _template_cache[path]

    @fastapi_app.get("/", response_class=HTMLResponse)
    async def home():
        return HTMLResponse(content=_load_template("dashboard_main.html"))

    @fastapi_app.get("/dashboard", response_class=HTMLResponse)
    async def dashboard():
        return HTMLResponse(content=_load_template("dashboard_main.html"))

    @fastapi_app.get("/verify", response_class=HTMLResponse)
    async def verify_page():
        return HTMLResponse(content=_load_template("verification_enhanced.html"))

    @fastapi_app.get("/app", response_class=HTMLResponse)
    async def app_page():
        return HTMLResponse(content=_load_template("dashboard_main.html"))

    @fastapi_app.get("/dashboard-app", response_class=HTMLResponse)
    async def dashboard_app():
        return HTMLResponse(content=_load_template("verification_enhanced.html"))

    @fastapi_app.get("/dashboard-old", response_class=HTMLResponse)
    async def dashboard_old():
        return HTMLResponse(content=_load_template("verification_dashboard_v2.html"))

    @fastapi_app.get("/verify-sms", response_class=HTMLResponse)
    async def verify_sms_prod():
        return HTMLResponse(content=_load_template("verification_prod.html"))

    @fastapi_app.get("/auth/login", response_class=HTMLResponse)
    async def login_page():
        return HTMLResponse(content=_load_template("login.html"))

    @fastapi_app.get("/auth/forgot-password", response_class=HTMLResponse)
    async def forgot_password_page():
        return HTMLResponse(content=_load_template("password_reset.html"))

    @fastapi_app.get("/auth/reset-password", response_class=HTMLResponse)
    async def reset_password_page():
        return HTMLResponse(content=_load_template("password_reset_confirm.html"))

    @fastapi_app.get("/reviews", response_class=HTMLResponse)
    async def reviews_page():
        return HTMLResponse(content=_load_template("reviews.html"))

    @fastapi_app.get("/dashboard/legacy", response_class=HTMLResponse)
    async def legacy_dashboard():
        return HTMLResponse(content=_load_template("dashboard_fixed.html"))

    @fastapi_app.get("/affiliate", response_class=HTMLResponse)
    async def affiliate_page():
        return HTMLResponse(content=_load_template("affiliate_program.html"))

    @fastapi_app.get("/affiliate/dashboard", response_class=HTMLResponse)
    async def affiliate_dashboard():
        return HTMLResponse(content=_load_template("affiliate_dashboard.html"))

    @fastapi_app.get("/whitelabel/setup", response_class=HTMLResponse)
    async def whitelabel_setup():
        return HTMLResponse(content=_load_template("whitelabel_setup.html"))

    @fastapi_app.get("/reseller/dashboard", response_class=HTMLResponse)
    async def reseller_dashboard_page():
        return HTMLResponse(content=_load_template("reseller_dashboard.html"))

    @fastapi_app.get("/rentals", response_class=HTMLResponse)
    async def rental_dashboard_page():
        return HTMLResponse(content=_load_template("rental_dashboard.html"))

    @fastapi_app.get("/history", response_class=HTMLResponse)
    async def history_page():
        return HTMLResponse(content=_load_template("history_advanced.html"))

    @fastapi_app.get("/bulk", response_class=HTMLResponse)
    async def bulk_purchase_page():
        return HTMLResponse(content=_load_template("bulk_purchase.html"))

    @fastapi_app.get("/sms-history", response_class=HTMLResponse)
    async def sms_history_page():
        return HTMLResponse(content=_load_template("sms_history.html"))

    @fastapi_app.on_event("startup")
    async def startup_event():
        """Initialize connections on startup."""
        await cache.connect()

        import asyncio

        from app.core.config import settings
        from app.services.sms_polling_service import sms_polling_service

        async def _run_sms_service_supervisor():
            logger = get_logger("sms-supervisor")
            while True:
                try:
                    await asyncio.wait_for(
                        sms_polling_service.start_background_service(),
                        timeout=settings.async_task_timeout_seconds,
                    )
                    logger.info("SMS polling service exited; restarting supervisor in 5s")
                    await asyncio.sleep(5)
                except asyncio.TimeoutError:
                    logger.warning("SMS polling service timed out; restarting")
                    await asyncio.sleep(2)
                except asyncio.CancelledError:
                    logger.info("SMS supervisor cancelled")
                    break
                except Exception as e:
                    logger.error(f"SMS supervisor error: {e}")
                    await asyncio.sleep(5)

        asyncio.create_task(_run_sms_service_supervisor())

    @fastapi_app.on_event("shutdown")
    async def shutdown_event():
        """Graceful cleanup on shutdown."""
        logger = get_logger("shutdown")
        logger.info("Starting graceful shutdown")

        try:
            from app.services.sms_polling_service import sms_polling_service
            await sms_polling_service.stop_background_service()
            logger.info("SMS polling service stopped")

            await cache.disconnect()
            logger.info("Cache disconnected")

            engine.dispose()
            logger.info("Database connections disposed")

            logger.info("Graceful shutdown completed")
        except Exception as e:
            logger.error("Error during shutdown", error=str(e))

    return fastapi_app


app = create_app()
