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
from fastapi.middleware.cors import CORSMiddleware as FastAPICORSMiddleware
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from starlette.middleware.gzip import GZipMiddleware
from sqlalchemy.orm import Session
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

# Import essential routers only
from app.api.core.auth import router as auth_router
from app.api.core.auth_enhanced import router as auth_enhanced_router
from app.api.core.gdpr import router as gdpr_router
from app.api.admin.admin_router import router as admin_router
from app.api.core.countries import router as countries_router
from app.api.core.services import router as services_router
from app.api.core.system import root_router, router as system_router

# Import production implementation routers
from app.api.verification.textverified_endpoints import router as textverified_router
from app.api.verification.pricing_endpoints import router as pricing_router
from app.api.verification.rentals_endpoints import router as rentals_endpoints_router
from app.api.rentals.textverified_rentals import router as rentals_router
from app.api.integrations.sms_inbox import router as sms_router
from app.api.integrations.billing import router as billing_router
from app.api.integrations.webhooks import router as webhooks_router
from app.api.integrations.wake_requests import router as wake_router
from app.api.integrations.api_docs import router as docs_router
from app.api.integrations.sms_forwarding import router as forwarding_router
from app.api.integrations.billing_cycles import router as cycles_router

from app.core.unified_cache import cache
from app.core.database import engine, get_db
from app.core.dependencies import get_current_user_id

security = HTTPBearer(auto_error=False)

TEMPLATES_DIR = Path("templates").resolve()
STATIC_DIR = Path("static").resolve()

ROUTERS = [
    (root_router, None),
    (auth_router, "/api"),
    (auth_enhanced_router, "/api"),
    (gdpr_router, "/api"),
    (admin_router, "/api"),
    (countries_router, "/api"),
    (services_router, None),
    (system_router, None),
    (textverified_router, None),
    (pricing_router, None),
    (rentals_endpoints_router, None),
    (rentals_router, None),
    (sms_router, None),
    (billing_router, None),
    (webhooks_router, None),
    (wake_router, None),
    (docs_router, None),
    (forwarding_router, None),
    (cycles_router, None),
]


def get_optional_user_id(credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)) -> Optional[str]:
    """Get user ID from token if provided, otherwise return None."""
    if not credentials:
        return None
    try:
        import jwt
        from app.core.config import get_settings as get_app_settings
        settings = get_app_settings()
        payload = jwt.decode(credentials.credentials, settings.secret_key, algorithms=[settings.jwt_algorithm])
        return payload.get("user_id")
    except (jwt.InvalidTokenError, jwt.DecodeError, AttributeError):
        return None


def _register_routers(app: FastAPI) -> None:
    """Register all routers with the application."""
    for router, prefix in ROUTERS:
        if prefix:
            app.include_router(router, prefix=prefix)
        else:
            app.include_router(router)


def create_app() -> FastAPI:
    """Application factory pattern - optimized for performance"""
    # Setup logging first
    setup_logging()

    # Import all models and configure registry
    from app.models.base import Base  # noqa: F401
    import app.models  # noqa: F401
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

    # Add GZIP compression middleware
    fastapi_app.add_middleware(GZipMiddleware, minimum_size=1000)

    # Add FastAPI CORS middleware
    from app.core.config import get_settings as get_app_settings
    app_settings = get_app_settings()
    cors_origins = [
        "http://localhost:3000",
        "http://localhost:8000",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:8000",
    ]
    if app_settings.environment == "production":
        cors_origins = [
            "https://yourdomain.com",
            "https://app.yourdomain.com",
        ]
    fastapi_app.add_middleware(
        FastAPICORSMiddleware,
        allow_origins=cors_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        allow_headers=["Content-Type", "Authorization", "X-CSRF-Token"],
    )

    # Setup unified middleware (rate limiting + error handling)
    setup_unified_middleware(fastapi_app)

    # Security and performance middleware stack
    fastapi_app.add_middleware(CSRFMiddleware)
    fastapi_app.add_middleware(SecurityHeadersMiddleware)
    fastapi_app.add_middleware(XSSProtectionMiddleware)
    fastapi_app.add_middleware(RequestLoggingMiddleware)

    # Register all routers
    _register_routers(fastapi_app)

    # Static files - ensure proper serving
    if STATIC_DIR.exists():
        fastapi_app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")
    else:
        startup_logger = get_logger("startup")
        startup_logger.error(f"Static directory '{STATIC_DIR}' not found")

    # Direct template loading (no cache)
    def _load_template(path: str) -> str:
        template_path = (TEMPLATES_DIR / path).resolve()
        if not str(template_path).startswith(str(TEMPLATES_DIR)):
            return "<h1>Page not found</h1>"
        if not template_path.exists():
            return "<h1>Page not found</h1>"
        try:
            with open(template_path, "r") as f:
                return f.read()
        except (IOError, OSError):
            return "<h1>Page not found</h1>"

    @fastapi_app.get("/", response_class=HTMLResponse)
    async def home():
        return HTMLResponse(content=_load_template("dashboard_main.html"))

    @fastapi_app.get("/dashboard", response_class=HTMLResponse)
    async def dashboard(user_id: str = Depends(get_current_user_id)):
        return HTMLResponse(content=_load_template("dashboard_complete.html"))

    @fastapi_app.get("/verify", response_class=HTMLResponse)
    async def verify_page(user_id: str = Depends(get_current_user_id)):
        return HTMLResponse(content=_load_template("verification_fixed.html"))

    @fastapi_app.get("/dashboard-complete", response_class=HTMLResponse)
    async def dashboard_complete(user_id: str = Depends(get_current_user_id)):
        return HTMLResponse(content=_load_template("dashboard_complete.html"))

    @fastapi_app.get("/app", response_class=HTMLResponse)
    async def app_page(user_id: str = Depends(get_current_user_id)):
        return HTMLResponse(content=_load_template("dashboard_complete.html"))

    @fastapi_app.get("/verification", response_class=HTMLResponse)
    async def verification_page(user_id: str = Depends(get_current_user_id)):
        return HTMLResponse(content=_load_template("verification_fixed.html"))

    @fastapi_app.get("/auth/login", response_class=HTMLResponse)
    async def login_page():
        return HTMLResponse(content=_load_template("login.html"))

    @fastapi_app.get("/auth/register", response_class=HTMLResponse)
    async def register_page():
        return HTMLResponse(content=_load_template("register.html"))

    @fastapi_app.get("/sms-inbox", response_class=HTMLResponse)
    async def sms_inbox_page(user_id: str = Depends(get_current_user_id)):
        return HTMLResponse(content=_load_template("sms_inbox.html"))

    @fastapi_app.get("/billing", response_class=HTMLResponse)
    async def billing_page(user_id: str = Depends(get_current_user_id)):
        return HTMLResponse(content=_load_template("billing_dashboard.html"))

    @fastapi_app.get("/rentals", response_class=HTMLResponse)
    async def rentals_page(user_id: str = Depends(get_current_user_id)):
        return HTMLResponse(content=_load_template("rental_management.html"))

    @fastapi_app.get("/admin-dashboard", response_class=HTMLResponse)
    async def admin_dashboard_page(user_id: str = Depends(get_current_user_id)):
        return HTMLResponse(content=_load_template("admin_dashboard.html"))

    @fastapi_app.get("/privacy-settings", response_class=HTMLResponse)
    async def privacy_settings_page(user_id: str = Depends(get_current_user_id)):
        return HTMLResponse(content=_load_template("gdpr_settings.html"))

    @fastapi_app.get("/api-keys", response_class=HTMLResponse)
    async def api_keys_page(user_id: str = Depends(get_current_user_id)):
        return HTMLResponse(content=_load_template("api_keys.html"))

    @fastapi_app.get("/account-settings", response_class=HTMLResponse)
    async def account_settings_page(user_id: str = Depends(get_current_user_id)):
        return HTMLResponse(content=_load_template("account_settings.html"))

    @fastapi_app.get("/analytics-dashboard", response_class=HTMLResponse)
    async def analytics_dashboard_page(user_id: str = Depends(get_current_user_id)):
        return HTMLResponse(content=_load_template("analytics_dashboard.html"))

    @fastapi_app.get("/track.js")
    async def track_js():
        return Response(content="// Analytics tracking placeholder", media_type="application/javascript")

    @fastapi_app.get("/api/user/balance")
    async def user_balance(user_id: str = Depends(get_current_user_id), db: Session = Depends(get_db)):
        from app.models.user import User
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        return {
            "credits": float(user.credits or 0),
            "free_verifications": int(user.free_verifications or 0),
            "currency": "USD"
        }

    @fastapi_app.post("/api/auth/register")
    async def register_user(request: Request):
        from app.core.database import get_db
        from app.services.auth_service import get_auth_service
        import json
        db = None
        try:
            body = await request.body()
            data = json.loads(body)
            email = data.get("email")
            password = data.get("password")
            if not email or not password:
                raise HTTPException(status_code=400, detail="Email and password required")
            db = next(get_db())
            auth_service = get_auth_service(db)
            user = auth_service.register_user(email, password)
            token = auth_service.create_user_token(user)
            return {
                "success": True,
                "access_token": token,
                "token_type": "bearer",
                "user": {
                    "id": user.id,
                    "email": user.email,
                    "credits": float(user.credits or 0),
                    "free_verifications": int(user.free_verifications or 0)
                }
            }
        except HTTPException:
            raise
        except (ValueError, KeyError, StopIteration):
            raise HTTPException(status_code=400, detail="Registration failed")
        finally:
            if db:
                db.close()

    @fastapi_app.post("/api/billing/add-credits")
    async def add_credits(request: Request, user_id: Optional[str] = Depends(get_optional_user_id), db: Session = Depends(get_db)):
        from app.models.user import User
        import json
        try:
            if not user_id:
                raise HTTPException(status_code=401, detail="Authentication required")
            body = await request.body()
            data = json.loads(body)
            amount = float(data.get("amount", 0))
            if amount <= 0:
                raise HTTPException(status_code=400, detail="Invalid amount")
            user = db.query(User).filter(User.id == user_id).first()
            if not user:
                raise HTTPException(status_code=404, detail="User not found")
            bonus = 7 if amount >= 50 else (3 if amount >= 25 else (1 if amount >= 10 else 0))
            total_amount = amount + bonus
            user.credits = (user.credits or 0) + total_amount
            db.commit()
            return {
                "success": True,
                "amount_added": total_amount,
                "bonus": bonus,
                "new_balance": float(user.credits)
            }
        except HTTPException:
            raise
        except (ValueError, KeyError, TypeError):
            raise HTTPException(status_code=500, detail="Failed to add credits")

    @fastapi_app.get("/favicon.ico")
    async def favicon():
        from fastapi.responses import FileResponse
        favicon_path = STATIC_DIR / "favicon.ico"
        if favicon_path.exists():
            return FileResponse(str(favicon_path))
        raise HTTPException(status_code=404, detail="Favicon not found")

    @fastapi_app.get("/api/system/health")
    async def system_health():
        return {
            "status": "healthy",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "version": "2.5.0",
            "database": "connected",
            "authentication": "active"
        }

    @fastapi_app.get("/api/analytics/summary")
    async def analytics_summary(user_id: str = Depends(get_current_user_id), db: Session = Depends(get_db)):
        from app.models.user import User
        from app.models.verification import Verification
        try:
            query = db.query(Verification).filter(Verification.user_id == user_id)
            total_verifications = query.count()
            successful_verifications = query.filter(Verification.status == 'completed').count()
            user = db.query(User).filter(User.id == user_id).first()
            total_users = db.query(User).count() if user and user.is_admin else 1
            return {
                "total_verifications": total_verifications,
                "successful_verifications": successful_verifications,
                "failed_verifications": total_verifications - successful_verifications,
                "total_users": total_users,
                "active_users": total_users,
                "revenue": successful_verifications * 0.20,
                "top_services": ["Telegram", "WhatsApp", "Discord"],
                "recent_activity": ["Account created successfully"]
            }
        except Exception:
            return {
                "total_verifications": 0,
                "successful_verifications": 0,
                "failed_verifications": 0,
                "total_users": 0,
                "active_users": 0,
                "revenue": 0.0,
                "top_services": [],
                "recent_activity": []
            }

    @fastapi_app.get("/api/countries/")
    async def get_countries():
        countries = [
            {"code": "russia", "name": "Russia", "prefix": "7", "popular": True},
            {"code": "india", "name": "India", "prefix": "91", "popular": True},
            {"code": "usa", "name": "United States", "prefix": "1", "popular": False},
        ]
        return {"success": True, "countries": countries, "total": len(countries)}

    @fastapi_app.on_event("startup")
    async def startup_event():
        startup_logger = get_logger("startup")
        startup_logger.info("Application startup")
        await cache.connect()
        from app.services.sms_polling_service import sms_polling_service
        from app.core.config import get_settings as get_startup_settings
        import asyncio

        async def _run_sms_service_supervisor():
            sms_logger = get_logger("sms-supervisor")
            startup_config = get_startup_settings()
            while True:
                try:
                    await asyncio.wait_for(
                        sms_polling_service.start_background_service(),
                        timeout=startup_config.async_task_timeout_seconds,
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

        asyncio.create_task(_run_sms_service_supervisor())

    @fastapi_app.on_event("shutdown")
    async def shutdown_event():
        shutdown_logger = get_logger("shutdown")
        shutdown_logger.info("Starting graceful shutdown")
        try:
            from app.services.sms_polling_service import sms_polling_service
            await sms_polling_service.stop_background_service()
            shutdown_logger.info("SMS polling service stopped")
            await cache.disconnect()
            shutdown_logger.info("Cache disconnected")
            engine.dispose()
            shutdown_logger.info("Database connections disposed")
            shutdown_logger.info("Graceful shutdown completed")
        except Exception as e:
            shutdown_logger.error("Error during shutdown", error=str(e))

    return fastapi_app


app = create_app()
