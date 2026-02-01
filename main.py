"""
Namaskah SMS - Optimized Application Factory
"""

from datetime import datetime
from pathlib import Path
from typing import Optional
from fastapi import Depends, FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware as FastAPICORSMiddleware
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from starlette.middleware.gzip import GZipMiddleware
from app.api.admin.router import router as admin_router
from app.api.billing.router import router as billing_router
from app.api.core.router import router as core_router
from app.api.health import router as health_router
from app.api.preview_router import router as preview_router
from app.api.routes_consolidated import router as routes_router
from app.api.v1.router import v1_router
from app.api.verification.area_code_endpoints import router as area_code_router
from app.api.verification.carrier_endpoints import router as carrier_router
from app.api.verification.pricing_endpoints import router as pricing_router
from app.api.verification.router import router as verification_router
from app.api.websocket_endpoints import router as websocket_router
from app.core.config import get_settings
from app.core.database import get_db
from app.core.lifespan import lifespan
from app.core.logging import get_logger, setup_logging
from app.core.unified_error_handling import setup_unified_middleware
from app.core.unified_rate_limiting import setup_unified_rate_limiting
from app.middleware.csrf_middleware import CSRFMiddleware
from app.middleware.logging import RequestLoggingMiddleware
from app.middleware.security import SecurityHeadersMiddleware
from app.middleware.xss_protection import XSSProtectionMiddleware
import jwt
from app.models.base import Base
import uvicorn


# Import modular routers

security = HTTPBearer(auto_error=False)
TEMPLATES_DIR = Path("templates").resolve()
STATIC_DIR = Path("static").resolve()


def get_optional_user_id(

    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
) -> Optional[str]:
    """Get user ID from token if provided, otherwise return None."""
    if not credentials:
        return None
    try:
        settings = get_settings()
        payload = jwt.decode(
            credentials.credentials,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm],
        )
        return payload.get("user_id")
    except Exception:
        return None


def create_app() -> FastAPI:

    """Application factory pattern."""
    setup_logging()
    get_logger("startup")
    settings = get_settings()

    # Initialize models

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

    cors_origins = [
        "http://localhost:3000",
        "http://localhost:8000",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:8000",
    ]
    if settings.environment == "production":
        cors_origins = list(
            set(
                [
                    settings.base_url,
                    settings.base_url.replace("https://", "https://app."),
                ]
            )
        )

    fastapi_app.add_middleware(
        FastAPICORSMiddleware,
        allow_origins=cors_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        allow_headers=["Content-Type", "Authorization", "X-CSRF-Token"],
    )

    setup_unified_middleware(fastapi_app)
    setup_unified_rate_limiting(fastapi_app)

    @fastapi_app.middleware("http")
    async def fix_mime_types(request: Request, call_next):
        response = await call_next(request)
        path = request.url.path
        if path.endswith(".css"):
            response.headers["content-type"] = "text/css; charset=utf-8"
        elif path.endswith(".js"):
            response.headers["content-type"] = "application/javascript; charset=utf-8"
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
    # Health checks (must be first for monitoring)
    fastapi_app.include_router(health_router)

    # WebSocket endpoints (real-time notifications)
    fastapi_app.include_router(websocket_router)

    # Modular Routers (Legacy - Deprecated)
    fastapi_app.include_router(core_router, deprecated=True)
    fastapi_app.include_router(admin_router, deprecated=True)
    fastapi_app.include_router(billing_router, prefix="/api", deprecated=True)
    fastapi_app.include_router(verification_router, prefix="/api", deprecated=True)

    # Verification Feature Routers
    fastapi_app.include_router(area_code_router, prefix="/api")
    fastapi_app.include_router(carrier_router, prefix="/api")
    fastapi_app.include_router(pricing_router, prefix="/api")

    # Version 1 API
    fastapi_app.include_router(v1_router)

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
            "templates": {
                "count": (
                    len(list(TEMPLATES_DIR.glob("*.html")))
                    if TEMPLATES_DIR.exists()
                    else 0
                )
            },
        }

    return fastapi_app


app = create_app()

if __name__ == "__main__":

    # Using port 9527 to avoid conflicts with common ports (8000, 8001, 8080, 3000, 5000)
    uvicorn.run("main:app", host="0.0.0.0", port=9527, reload=True)
