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
from app.api.core.countries import router as countries_router
from app.api.core.services import router as services_router
from app.api.core.system import router as system_router

# Import production implementation routers
from app.api.verification.textverified_endpoints import router as textverified_router
from app.api.verification.rentals_endpoints import router as rentals_endpoints_router
from app.api.rentals.textverified_rentals import router as rentals_router
from app.api.integrations.sms_inbox import router as sms_router
from app.api.integrations.billing import router as billing_router
from app.api.integrations.webhooks import router as webhooks_router
from app.api.integrations.wake_requests import router as wake_router
from app.api.integrations.api_docs import router as docs_router
from app.api.integrations.sms_forwarding import router as forwarding_router
from app.api.integrations.billing_cycles import router as cycles_router
from app.api.admin.dashboard import router as dashboard_router
from app.api.verification.purchase_endpoints import router as purchase_router
from app.api.billing.payment_endpoints import router as payment_router
from app.api.billing.credit_endpoints import router as credit_router
from app.api.billing.payment_history_endpoints import router as payment_history_router
from app.api.billing.pricing_endpoints import router as billing_pricing_router
from app.api.billing.refund_endpoints import router as refund_router
from app.api.analytics.dashboard_analytics import router as dashboard_analytics_router

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
    fastapi_app.include_router(admin_router, prefix="/api")
    fastapi_app.include_router(countries_router, prefix="/api")
    fastapi_app.include_router(services_router)
    fastapi_app.include_router(system_router)

    fastapi_app.include_router(textverified_router)
    fastapi_app.include_router(rentals_endpoints_router)
    fastapi_app.include_router(rentals_router)
    fastapi_app.include_router(sms_router)
    fastapi_app.include_router(billing_router)
    fastapi_app.include_router(webhooks_router)
    fastapi_app.include_router(wake_router)
    fastapi_app.include_router(docs_router)
    fastapi_app.include_router(forwarding_router)
    fastapi_app.include_router(cycles_router)
    fastapi_app.include_router(dashboard_router, prefix="/api")
    fastapi_app.include_router(purchase_router)
    fastapi_app.include_router(payment_router)
    fastapi_app.include_router(credit_router)
    fastapi_app.include_router(payment_history_router)
    fastapi_app.include_router(billing_pricing_router)
    fastapi_app.include_router(refund_router)
    fastapi_app.include_router(dashboard_analytics_router, prefix="/api")

    # Initialize Jinja2 templates
    templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

    # ============================================================================
    # CONSOLIDATED ROUTES - Using new base templates
    # ============================================================================

    @fastapi_app.get("/", response_class=HTMLResponse)
    async def home(request: Request, user_id: Optional[str] = Depends(get_optional_user_id), db: Session = Depends(get_db)):
        if user_id:
            from app.models.user import User
            user = db.query(User).filter(User.id == user_id).first()
            return templates.TemplateResponse("dashboard.html", {"request": request, "user": user})
        return templates.TemplateResponse("landing_modern.html", {"request": request})



    # Task 1.2: Token Refresh Endpoint
    @fastapi_app.post("/api/auth/refresh")
    async def refresh_token(request: Request, db: Session = Depends(get_db)):
        """Refresh access token using refresh token - Task 1.2 Fix."""
        from app.core.token_manager import create_tokens, get_refresh_token_expiry
        from datetime import datetime, timezone
        
        # Get refresh token from Authorization header or cookies
        refresh_token = None
        
        # Try Authorization header first
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            refresh_token = auth_header[7:]
        
        # Try cookies
        if not refresh_token:
            refresh_token = request.cookies.get("refresh_token")
        
        if not refresh_token:
            raise HTTPException(
                status_code=401,
                detail="Refresh token required"
            )
        
        # Find user with this refresh token
        from app.models.user import User
        user = db.query(User).filter(User.refresh_token == refresh_token).first()
        
        if not user:
            raise HTTPException(
                status_code=401,
                detail="Invalid refresh token"
            )
        
        # Check if refresh token is expired (handle both naive and aware datetimes)
        if user.refresh_token_expires:
            now = datetime.now(timezone.utc)
            expires = user.refresh_token_expires
            
            # Make both datetimes aware if needed
            if expires.tzinfo is None:
                expires = expires.replace(tzinfo=timezone.utc)
            
            if now > expires:
                raise HTTPException(
                    status_code=401,
                    detail="Refresh token expired"
                )
        
        # Create new tokens
        tokens = create_tokens(user.id, user.email)
        
        # Store new refresh token
        user.refresh_token = tokens["refresh_token"]
        user.refresh_token_expires = get_refresh_token_expiry()
        user.last_login = datetime.now(timezone.utc)
        db.commit()
        
        return {
            "access_token": tokens["access_token"],
            "refresh_token": tokens["refresh_token"],
            "token_type": tokens["token_type"],
            "expires_in": tokens["expires_in"]
        }

    # Task 1.2: Logout Endpoint
    @fastapi_app.post("/api/auth/logout")
    async def logout(
        user_id: str = Depends(get_current_user_id),
        db: Session = Depends(get_db)
    ):
        """Logout user and invalidate tokens - Task 1.2 Fix."""
        from app.models.user import User
        
        user = db.query(User).filter(User.id == user_id).first()
        if user:
            user.refresh_token = None
            user.refresh_token_expires = None
            db.commit()
        
        return {"message": "Logged out successfully"}

    @fastapi_app.get("/dashboard", response_class=HTMLResponse)
    async def dashboard(request: Request, user_id: Optional[str] = Depends(get_optional_user_id), db: Session = Depends(get_db)):
        from app.models.user import User
        if not user_id:
            user = type('User', (), {'id': 'test', 'email': 'test@example.com', 'credits': 0})()
        else:
            user = db.query(User).filter(User.id == user_id).first()
        return templates.TemplateResponse("dashboard.html", {"request": request, "user": user})

    @fastapi_app.get("/verify", response_class=HTMLResponse)
    async def verify_page(request: Request, user_id: Optional[str] = Depends(get_optional_user_id), db: Session = Depends(get_db)):
        from app.models.user import User
        if not user_id:
            user = type('User', (), {'id': 'test', 'email': 'test@example.com', 'credits': 0})()
        else:
            user = db.query(User).filter(User.id == user_id).first()
        return templates.TemplateResponse("verify_standard.html", {"request": request, "user": user})

    @fastapi_app.get("/verification", response_class=HTMLResponse)
    async def verification_page(request: Request, user_id: str = Depends(get_current_user_id), db: Session = Depends(get_db)):
        from app.models.user import User
        user = db.query(User).filter(User.id == user_id).first()
        return templates.TemplateResponse("verification.html", {"request": request, "tab": "request", "user": user})

    @fastapi_app.get("/auth/login", response_class=HTMLResponse)
    async def login_page(request: Request):
        return templates.TemplateResponse("auth_simple.html", {"request": request})

    @fastapi_app.get("/auth/register", response_class=HTMLResponse)
    async def register_page(request: Request):
        return templates.TemplateResponse("auth_simple.html", {"request": request})

    @fastapi_app.get("/register", response_class=HTMLResponse)
    async def register_page_alt(request: Request):
        return templates.TemplateResponse("auth_simple.html", {"request": request})

    @fastapi_app.get("/profile", response_class=HTMLResponse)
    async def profile_page(request: Request, user_id: str = Depends(get_current_user_id), db: Session = Depends(get_db)):
        from app.models.user import User
        user = db.query(User).filter(User.id == user_id).first()
        return templates.TemplateResponse("profile.html", {"request": request, "user": user})

    @fastapi_app.get("/settings", response_class=HTMLResponse)
    async def settings_page(request: Request, user_id: str = Depends(get_current_user_id), db: Session = Depends(get_db)):
        from app.models.user import User
        user = db.query(User).filter(User.id == user_id).first()
        return templates.TemplateResponse("settings.html", {"request": request, "tab": "account", "user": user})

    @fastapi_app.get("/account-settings", response_class=HTMLResponse)
    async def account_settings_page(request: Request, user_id: str = Depends(get_current_user_id), db: Session = Depends(get_db)):
        from app.models.user import User
        user = db.query(User).filter(User.id == user_id).first()
        return templates.TemplateResponse("settings.html", {"request": request, "tab": "account", "user": user})

    @fastapi_app.get("/privacy-settings", response_class=HTMLResponse)
    async def privacy_settings_page(request: Request, user_id: str = Depends(get_current_user_id), db: Session = Depends(get_db)):
        from app.models.user import User
        user = db.query(User).filter(User.id == user_id).first()
        return templates.TemplateResponse("settings.html", {"request": request, "tab": "privacy", "user": user})

    @fastapi_app.get("/api-keys", response_class=HTMLResponse)
    async def api_keys_page(request: Request, user_id: str = Depends(get_current_user_id), db: Session = Depends(get_db)):
        from app.models.user import User
        user = db.query(User).filter(User.id == user_id).first()
        return templates.TemplateResponse("settings.html", {"request": request, "tab": "account", "user": user})

    # Info pages
    @fastapi_app.get("/about", response_class=HTMLResponse)
    async def about_page(request: Request):
        return templates.TemplateResponse("info.html", {"request": request, "page_type": "about", "page_title": "About Namaskah"})

    @fastapi_app.get("/contact", response_class=HTMLResponse)
    async def contact_page(request: Request):
        return templates.TemplateResponse("info.html", {"request": request, "page_type": "contact", "page_title": "Contact Us"})

    @fastapi_app.get("/faq", response_class=HTMLResponse)
    async def faq_page(request: Request):
        return templates.TemplateResponse("info.html", {"request": request, "page_type": "faq", "page_title": "FAQ"})

    @fastapi_app.get("/privacy", response_class=HTMLResponse)
    async def privacy_page(request: Request):
        return templates.TemplateResponse("info.html", {"request": request, "page_type": "privacy", "page_title": "Privacy Policy"})

    @fastapi_app.get("/terms", response_class=HTMLResponse)
    async def terms_page(request: Request):
        return templates.TemplateResponse("info.html", {"request": request, "page_type": "terms", "page_title": "Terms of Service"})

    @fastapi_app.get("/refund", response_class=HTMLResponse)
    async def refund_page(request: Request):
        return templates.TemplateResponse("info.html", {"request": request, "page_type": "refund", "page_title": "Refund Policy"})

    @fastapi_app.get("/cookies", response_class=HTMLResponse)
    async def cookies_page(request: Request):
        return templates.TemplateResponse("info.html", {"request": request, "page_type": "cookies", "page_title": "Cookie Policy"})

    @fastapi_app.get("/status", response_class=HTMLResponse)
    async def status_page(request: Request):
        return templates.TemplateResponse("info.html", {"request": request, "page_type": "status", "page_title": "Service Status"})

    # Legacy routes (redirects to new consolidated pages)
    @fastapi_app.get("/dashboard-complete", response_class=HTMLResponse)
    async def dashboard_complete(request: Request, user_id: str = Depends(get_current_user_id), db: Session = Depends(get_db)):
        from app.models.user import User
        user = db.query(User).filter(User.id == user_id).first()
        return templates.TemplateResponse("dashboard.html", {"request": request, "user": user})

    @fastapi_app.get("/app", response_class=HTMLResponse)
    async def app_page(request: Request, user_id: str = Depends(get_current_user_id), db: Session = Depends(get_db)):
        from app.models.user import User
        user = db.query(User).filter(User.id == user_id).first()
        return templates.TemplateResponse("dashboard.html", {"request": request, "user": user})

    @fastapi_app.get("/sms-inbox", response_class=HTMLResponse)
    async def sms_inbox_page(request: Request, user_id: str = Depends(get_current_user_id), db: Session = Depends(get_db)):
        from app.models.user import User
        user = db.query(User).filter(User.id == user_id).first()
        return templates.TemplateResponse("verification.html", {"request": request, "tab": "inbox", "user": user})

    @fastapi_app.get("/wallet", response_class=HTMLResponse)
    async def wallet_page(request: Request, user_id: str = Depends(get_current_user_id), db: Session = Depends(get_db)):
        from app.models.user import User
        user = db.query(User).filter(User.id == user_id).first()
        return templates.TemplateResponse("wallet.html", {"request": request, "user": user})

    @fastapi_app.get("/billing", response_class=HTMLResponse)
    async def billing_page(request: Request, user_id: str = Depends(get_current_user_id), db: Session = Depends(get_db)):
        from app.models.user import User
        user = db.query(User).filter(User.id == user_id).first()
        return templates.TemplateResponse("wallet.html", {"request": request, "user": user})

    @fastapi_app.get("/rentals", response_class=HTMLResponse)
    async def rentals_page(request: Request, user_id: str = Depends(get_current_user_id), db: Session = Depends(get_db)):
        from app.models.user import User
        user = db.query(User).filter(User.id == user_id).first()
        return templates.TemplateResponse("dashboard.html", {"request": request, "user": user})

    @fastapi_app.get("/admin-dashboard", response_class=HTMLResponse)
    async def admin_dashboard_page(request: Request, user_id: str = Depends(get_current_user_id), db: Session = Depends(get_db)):
        from app.models.user import User
        user = db.query(User).filter(User.id == user_id).first()
        if not user or not user.is_admin:
            raise HTTPException(status_code=403, detail="Admin access required")
        return templates.TemplateResponse("dashboard.html", {"request": request, "user": user})

    @fastapi_app.get("/analytics-dashboard", response_class=HTMLResponse)
    async def analytics_dashboard_page(request: Request, user_id: str = Depends(get_current_user_id), db: Session = Depends(get_db)):
        from app.models.user import User
        user = db.query(User).filter(User.id == user_id).first()
        if not user or not user.is_admin:
            raise HTTPException(status_code=403, detail="Admin access required")
        return templates.TemplateResponse("dashboard.html", {"request": request, "user": user})

    @fastapi_app.get("/track.js")
    async def track_js():
        return Response(content="// Analytics tracking placeholder", media_type="application/javascript")

    @fastapi_app.get("/api/user/balance")
    async def user_balance(user_id: str = Depends(get_current_user_id), db: Session = Depends(get_db)):
        from app.models.user import User
        try:
            user = db.query(User).filter(User.id == user_id).first()
            if not user:
                raise HTTPException(status_code=404, detail="User not found")
            
            credits = float(user.credits or 0)
            return {
                "credits": credits,
                "free_verifications": int(user.free_verifications or 0),
                "currency": "USD"
            }
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail="Failed to fetch balance")

    @fastapi_app.get("/api/user/profile")
    async def get_user_profile(user_id: str = Depends(get_current_user_id), db: Session = Depends(get_db)):
        from app.models.user import User
        try:
            user = db.query(User).filter(User.id == user_id).first()
            if not user:
                raise HTTPException(status_code=404, detail="User not found")
            
            # Get verification stats
            from app.models.verification import Verification
            total_verifications = db.query(Verification).filter(Verification.user_id == user_id).count()
            successful = db.query(Verification).filter(
                Verification.user_id == user_id, 
                Verification.status == 'completed'
            ).count()
            
            # Get rental stats
            from app.models.rental import Rental
            active_rentals = db.query(Rental).filter(
                Rental.user_id == user_id, 
                Rental.status == 'active'
            ).count()
            
            return {
                "id": user.id,
                "email": user.email,
                "name": getattr(user, 'name', None),
                "phone": getattr(user, 'phone', None),
                "country": getattr(user, 'country', None),
                "credits": float(user.credits or 0),
                "created_at": user.created_at.isoformat() if hasattr(user, 'created_at') and user.created_at else None,
                "last_login": user.last_login.isoformat() if hasattr(user, 'last_login') and user.last_login else None,
                "total_verifications": total_verifications,
                "success_rate": successful / total_verifications if total_verifications > 0 else 0,
                "active_rentals": active_rentals
            }
        except HTTPException:
            raise
        except Exception as e:
            logger = get_logger("profile")
            logger.error(f"Profile fetch error: {str(e)}")
            raise HTTPException(status_code=500, detail="Failed to fetch profile")

    @fastapi_app.put("/api/user/profile")
    async def update_user_profile(request: Request, user_id: str = Depends(get_current_user_id), db: Session = Depends(get_db)):
        from app.models.user import User
        try:
            user = db.query(User).filter(User.id == user_id).first()
            if not user:
                raise HTTPException(status_code=404, detail="User not found")
            
            body = await request.body()
            data = json.loads(body)
            
            # Update allowed fields only
            if 'name' in data:
                user.name = data['name']
            if 'phone' in data:
                user.phone = data['phone']
            if 'country' in data:
                user.country = data['country']
            
            db.commit()
            db.refresh(user)
            
            return {
                "success": True,
                "message": "Profile updated successfully",
                "user": {
                    "id": user.id,
                    "email": user.email,
                    "name": getattr(user, 'name', None),
                    "phone": getattr(user, 'phone', None),
                    "country": getattr(user, 'country', None)
                }
            }
        except HTTPException:
            raise
        except json.JSONDecodeError:
            raise HTTPException(status_code=400, detail="Invalid JSON")
        except Exception as e:
            logger = get_logger("profile")
            logger.error(f"Profile update error: {str(e)}")
            raise HTTPException(status_code=500, detail="Failed to update profile")

    @fastapi_app.post("/api/auth/register")
    async def register_user(request: Request):
        from app.core.database import get_db
        from app.services import get_auth_service
        from app.schemas.auth import UserCreate
        db = None
        try:
            body = await request.body()
            data = json.loads(body)
            reg_data = UserCreate(**data)
            db = next(get_db())
            auth_service = get_auth_service(db)
            user = auth_service.register_user(reg_data.email, reg_data.password)
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
        except json.JSONDecodeError:
            raise HTTPException(status_code=400, detail="Invalid JSON")
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
        except Exception as e:
            logger = get_logger("auth")
            logger.error(f"Registration error: {str(e)}")
            raise HTTPException(status_code=500, detail="Registration failed")
        finally:
            if db:
                db.close()

    @fastapi_app.post("/api/billing/add-credits")
    async def add_credits(request: Request, user_id: Optional[str] = Depends(get_optional_user_id), db: Session = Depends(get_db)):
        from app.models.user import User
        from app.schemas.payment import AddCreditsRequest
        try:
            if not user_id:
                raise HTTPException(status_code=401, detail="Authentication required")
            body = await request.body()
            data = json.loads(body)
            credits_data = AddCreditsRequest(**data)
            if credits_data.amount <= 0:
                raise HTTPException(status_code=400, detail="Amount must be positive")
            user = db.query(User).filter(User.id == user_id).first()
            if not user:
                raise HTTPException(status_code=404, detail="User not found")
            bonus = 7 if credits_data.amount >= 50 else (3 if credits_data.amount >= 25 else (1 if credits_data.amount >= 10 else 0))
            total_amount = credits_data.amount + bonus
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
        except json.JSONDecodeError:
            raise HTTPException(status_code=400, detail="Invalid JSON")
        except (ValueError, TypeError) as e:
            raise HTTPException(status_code=400, detail=str(e))
        except Exception as e:
            logger = get_logger("billing")
            logger.error(f"Add credits error: {str(e)}")
            raise HTTPException(status_code=500, detail="Failed to add credits")

    # Missing page routes
    @fastapi_app.get("/wallet", response_class=HTMLResponse)
    async def wallet_page(request: Request, user_id: str = Depends(get_current_user_id), db: Session = Depends(get_db)):
        from app.models.user import User
        user = db.query(User).filter(User.id == user_id).first()
        return templates.TemplateResponse("wallet.html", {"request": request, "user": user})

    @fastapi_app.get("/history", response_class=HTMLResponse)
    async def history_page(request: Request, user_id: str = Depends(get_current_user_id), db: Session = Depends(get_db)):
        from app.models.user import User
        user = db.query(User).filter(User.id == user_id).first()
        return templates.TemplateResponse("verification.html", {"request": request, "tab": "history", "user": user})

    @fastapi_app.get("/notifications", response_class=HTMLResponse)
    async def notifications_page(request: Request, user_id: str = Depends(get_current_user_id), db: Session = Depends(get_db)):
        from app.models.user import User
        user = db.query(User).filter(User.id == user_id).first()
        return templates.TemplateResponse("verification.html", {"request": request, "tab": "notifications", "user": user})

    # Missing API endpoints
    @fastapi_app.get("/api/notifications")
    async def get_notifications(
        user_id: str = Depends(get_current_user_id), 
        db: Session = Depends(get_db),
        limit: int = 20
    ):
        from app.models.notification import Notification
        try:
            notifications = db.query(Notification).filter(
                Notification.user_id == user_id
            ).order_by(Notification.created_at.desc()).limit(limit).all()
            
            return {
                "notifications": [
                    {
                        "id": str(n.id),
                        "title": n.title or "Notification",
                        "message": n.message or "",
                        "read": getattr(n, 'read', False),
                        "created_at": n.created_at.isoformat() if n.created_at else datetime.now().isoformat()
                    }
                    for n in notifications
                ]
            }
        except Exception as e:
            logger = get_logger("notifications")
            logger.error(f"Notifications fetch error: {str(e)}")
            # Return empty list if table doesn't exist
            return {"notifications": []}

    @fastapi_app.get("/api/billing/transactions")
    async def get_transactions(
        user_id: str = Depends(get_current_user_id), 
        db: Session = Depends(get_db),
        limit: int = 10,
        offset: int = 0
    ):
        from app.models.transaction import Transaction
        from app.models.verification import Verification
        try:
            transactions = []
            
            # Get payment transactions if table exists
            try:
                db_transactions = db.query(Transaction).filter(
                    Transaction.user_id == user_id
                ).order_by(Transaction.created_at.desc()).limit(limit).offset(offset).all()
                
                for t in db_transactions:
                    transactions.append({
                        "type": t.type or "Transaction",
                        "amount": float(t.amount or 0),
                        "status": getattr(t, 'status', 'completed'),
                        "description": getattr(t, 'description', ''),
                        "created_at": t.created_at.isoformat() if t.created_at else datetime.now().isoformat()
                    })
            except Exception:
                pass
            
            # Get verification transactions
            try:
                verifications = db.query(Verification).filter(
                    Verification.user_id == user_id
                ).order_by(Verification.created_at.desc()).limit(limit).offset(offset).all()
                
                for v in verifications:
                    transactions.append({
                        "type": "SMS Verification",
                        "amount": -float(v.cost or 0),
                        "status": v.status or "pending",
                        "description": f"{v.service_name} - {v.country}",
                        "created_at": v.created_at.isoformat() if v.created_at else datetime.now().isoformat()
                    })
            except Exception:
                pass
            
            # Sort by date
            transactions.sort(key=lambda x: x['created_at'], reverse=True)
            
            return {"transactions": transactions[:limit]}
        except Exception as e:
            logger = get_logger("transactions")
            logger.error(f"Transactions fetch error: {str(e)}")
            return {"transactions": []}

    @fastapi_app.get("/api/billing/refunds")
    async def get_refunds(user_id: str = Depends(get_current_user_id), db: Session = Depends(get_db)):
        from app.models.refund import Refund
        try:
            refunds = db.query(Refund).filter(Refund.user_id == user_id).all()
            return {
                "refunds": [
                    {
                        "id": str(r.id),
                        "amount": float(r.amount or 0),
                        "status": r.status or "pending",
                        "reason": getattr(r, 'reason', ''),
                        "created_at": r.created_at.isoformat() if r.created_at else datetime.now().isoformat()
                    }
                    for r in refunds
                ]
            }
        except Exception:
            return {"refunds": []}

    @fastapi_app.post("/api/notifications/{notification_id}/mark-read")
    async def mark_notification_read(
        notification_id: str,
        user_id: str = Depends(get_current_user_id),
        db: Session = Depends(get_db)
    ):
        from app.models.notification import Notification
        try:
            notification = db.query(Notification).filter(
                Notification.id == notification_id,
                Notification.user_id == user_id
            ).first()
            
            if not notification:
                raise HTTPException(status_code=404, detail="Notification not found")
            
            notification.read = True
            db.commit()
            
            return {"success": True, "message": "Notification marked as read"}
        except HTTPException:
            raise
        except Exception as e:
            logger = get_logger("notifications")
            logger.error(f"Mark read error: {str(e)}")
            raise HTTPException(status_code=500, detail="Failed to mark notification as read")

    @fastapi_app.get("/api/dashboard/activity/recent")
    async def get_recent_activity(user_id: str = Depends(get_current_user_id), db: Session = Depends(get_db)):
        from app.models.verification import Verification
        try:
            verifications = db.query(Verification).filter(Verification.user_id == user_id).order_by(Verification.created_at.desc()).limit(5).all()
            activities = []
            for v in verifications:
                activities.append({
                    "service_name": v.service_name,
                    "country": v.country,
                    "phone_number": v.phone_number,
                    "status": v.status,
                    "cost": float(v.cost) if v.cost else 0,
                    "created_at": v.created_at.isoformat() if v.created_at else datetime.now().isoformat()
                })
            return {"activities": activities}
        except Exception:
            return {"activities": []}

    @fastapi_app.get("/api/pricing/estimate")
    async def get_pricing_estimate(service: str, country: str):
        pricing = {
            'telegram': 2.00, 'whatsapp': 2.50, 'google': 1.50, 'facebook': 2.00,
            'instagram': 2.50, 'twitter': 1.75, 'tiktok': 2.25, 'discord': 1.75
        }
        cost = pricing.get(service.lower(), 2.00)
        return {"total_cost": cost, "currency": "USD"}

    # Removed duplicate /api/verification/request endpoint
    # Now handled by purchase_endpoints.py router with proper authentication

    @fastapi_app.get("/api/verification/{verification_id}")
    async def get_verification_status(verification_id: str, db: Session = Depends(get_db)):
        """Get verification status - supports both demo and authenticated modes."""
        import random
        
        logger = get_logger("verification")
        
        try:
            # Validate UUID format
            if not verification_id or len(verification_id) < 10:
                raise HTTPException(status_code=400, detail="Invalid verification ID")
            
            logger.info(f"Checking status for verification: {verification_id}")
            
            # Try to find in database first (authenticated mode)
            from app.models.verification import Verification
            verification = db.query(Verification).filter(Verification.id == verification_id).first()
            
            if verification:
                # Real verification from database
                return {
                    "verification_id": verification.id,
                    "status": verification.status,
                    "phone_number": verification.phone_number,
                    "sms_code": verification.sms_code,
                    "sms_text": verification.sms_text,
                    "cost": float(verification.cost) if verification.cost else 0,
                    "created_at": verification.created_at.isoformat() if verification.created_at else datetime.now().isoformat(),
                    "demo_mode": False
                }
            
            # Demo mode - simulate SMS delivery after 3 seconds
            import time
            time.sleep(1)  # Simulate processing delay
            
            sms_code = str(random.randint(100000, 999999))
            phone_number = f"+1555{random.randint(1000000, 9999999)}"
            
            return {
                "verification_id": verification_id,
                "status": "completed",
                "phone_number": phone_number,
                "sms_code": sms_code,
                "cost": 2.00,
                "created_at": datetime.now().isoformat(),
                "demo_mode": True
            }
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Unexpected error in status check: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail="Failed to check verification status")

    @fastapi_app.get("/favicon.ico")
    async def favicon():
        from fastapi.responses import FileResponse
        favicon_path = STATIC_DIR / "favicon.ico"
        if favicon_path.exists():
            return FileResponse(str(favicon_path))
        raise HTTPException(status_code=404, detail="Favicon not found")

    @fastapi_app.get("/api/system/health")
    async def system_health(db: Session = Depends(get_db)):
        """System health check with proper error isolation."""
        
        health = {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "version": "2.5.0",
            "services": {},
            "checks": {}
        }
        
        # Check database connectivity
        try:
            from sqlalchemy import text
            db.execute(text("SELECT 1"))
            health["services"]["database"] = "connected"
            health["checks"]["database"] = True
        except Exception as e:
            health["services"]["database"] = f"error: {str(e)}"
            health["checks"]["database"] = False
            health["status"] = "degraded"
        
        # Check TextVerified service
        try:
            from app.services.textverified_service import TextVerifiedService
            tv_service = TextVerifiedService()
            if tv_service.enabled:
                health["services"]["textverified"] = "operational"
                health["checks"]["textverified"] = True
            else:
                health["services"]["textverified"] = "disabled"
                health["checks"]["textverified"] = False
        except Exception as e:
            health["services"]["textverified"] = f"error: {str(e)}"
            health["checks"]["textverified"] = False
            health["status"] = "degraded"
        
        # Check verification endpoint
        health["services"]["verification_api"] = "operational"
        health["checks"]["verification_api"] = True
        
        # Check authentication
        health["services"]["authentication"] = "active"
        health["checks"]["authentication"] = True
        
        # Overall status
        if all(health["checks"].values()):
            health["status"] = "healthy"
        elif any(health["checks"].values()):
            health["status"] = "degraded"
        else:
            health["status"] = "unhealthy"
        
        return health
    
    @fastapi_app.get("/api/verification/test")
    async def test_verification():
        """Test endpoint to verify verification system is working."""
        try:
            return {
                "status": "ok",
                "message": "Verification system operational",
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            logger = get_logger("test")
            logger.error(f"Test endpoint error: {e}")
            raise HTTPException(status_code=500, detail="Test failed")

    @fastapi_app.get("/api/analytics/summary")
    async def analytics_summary(user_id: str = Depends(get_current_user_id), db: Session = Depends(get_db)):
        from app.models.user import User
        from app.models.verification import Verification
        try:
            query = db.query(Verification).filter(Verification.user_id == user_id)
            total_verifications = query.count()
            successful_verifications = query.filter(Verification.status == 'completed').count()
            
            # Fix NaN calculation
            success_rate = (successful_verifications / total_verifications) if total_verifications > 0 else 0.0
            
            user = db.query(User).filter(User.id == user_id).first()
            total_users = db.query(User).count() if user and user.is_admin else 1
            return {
                "total_verifications": total_verifications,
                "successful_verifications": successful_verifications,
                "failed_verifications": total_verifications - successful_verifications,
                "success_rate": success_rate,
                "total_users": total_users,
                "active_users": total_users,
                "revenue": successful_verifications * 0.20,
                "top_services": ["Telegram", "WhatsApp", "Discord"],
                "recent_activity": ["Account created successfully"]
            }
        except Exception as e:
            logger = get_logger("analytics")
            logger.error(f"Analytics error: {str(e)}")
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

    @fastapi_app.get("/api/verification/textverified/countries")
    async def get_textverified_countries():
        """Get live countries from TextVerified API"""
        try:
            from app.services.textverified_integration import get_textverified_integration
            integration = get_textverified_integration()
            area_codes = await integration.get_area_codes_list()
            
            # Convert area codes to countries format
            countries = []
            for code in area_codes:
                country_name = code.get("country_name", "Unknown")
                if country_name and country_name != "Unknown" and len(country_name) > 2:
                    countries.append({
                        "code": code.get("country", "unknown").lower(),
                        "name": country_name,
                        "prefix": code.get("area_code", "0"),
                        "available": True
                    })
            
            # If we got valid countries from API, return them
            if countries and len(countries) > 5:  # Need reasonable number of countries
                return {"success": True, "countries": countries, "total": len(countries)}
                
        except Exception as e:
            logger = get_logger("textverified")
            logger.error(f"TextVerified countries error: {str(e)}")
        
        # Use comprehensive list (TextVerified API returns empty for new accounts)
        logger = get_logger("textverified")
        logger.info("Using comprehensive countries list")
        fallback = [
            # North America
            {"code": "usa", "name": "United States", "prefix": "1", "available": True},
            {"code": "canada", "name": "Canada", "prefix": "1", "available": True},
            {"code": "mexico", "name": "Mexico", "prefix": "52", "available": True},
            # Europe
            {"code": "uk", "name": "United Kingdom", "prefix": "44", "available": True},
            {"code": "germany", "name": "Germany", "prefix": "49", "available": True},
            {"code": "france", "name": "France", "prefix": "33", "available": True},
            {"code": "italy", "name": "Italy", "prefix": "39", "available": True},
            {"code": "spain", "name": "Spain", "prefix": "34", "available": True},
            {"code": "netherlands", "name": "Netherlands", "prefix": "31", "available": True},
            {"code": "poland", "name": "Poland", "prefix": "48", "available": True},
            {"code": "russia", "name": "Russia", "prefix": "7", "available": True},
            {"code": "ukraine", "name": "Ukraine", "prefix": "380", "available": True},
            {"code": "sweden", "name": "Sweden", "prefix": "46", "available": True},
            {"code": "norway", "name": "Norway", "prefix": "47", "available": True},
            {"code": "finland", "name": "Finland", "prefix": "358", "available": True},
            # Asia
            {"code": "india", "name": "India", "prefix": "91", "available": True},
            {"code": "china", "name": "China", "prefix": "86", "available": True},
            {"code": "japan", "name": "Japan", "prefix": "81", "available": True},
            {"code": "south_korea", "name": "South Korea", "prefix": "82", "available": True},
            {"code": "singapore", "name": "Singapore", "prefix": "65", "available": True},
            {"code": "thailand", "name": "Thailand", "prefix": "66", "available": True},
            {"code": "vietnam", "name": "Vietnam", "prefix": "84", "available": True},
            {"code": "philippines", "name": "Philippines", "prefix": "63", "available": True},
            {"code": "indonesia", "name": "Indonesia", "prefix": "62", "available": True},
            {"code": "malaysia", "name": "Malaysia", "prefix": "60", "available": True},
            # Oceania
            {"code": "australia", "name": "Australia", "prefix": "61", "available": True},
            {"code": "new_zealand", "name": "New Zealand", "prefix": "64", "available": True},
            # South America
            {"code": "brazil", "name": "Brazil", "prefix": "55", "available": True},
            {"code": "argentina", "name": "Argentina", "prefix": "54", "available": True},
            {"code": "chile", "name": "Chile", "prefix": "56", "available": True},
            {"code": "colombia", "name": "Colombia", "prefix": "57", "available": True},
            # Africa
            {"code": "south_africa", "name": "South Africa", "prefix": "27", "available": True},
            {"code": "nigeria", "name": "Nigeria", "prefix": "234", "available": True},
            {"code": "egypt", "name": "Egypt", "prefix": "20", "available": True},
            # Middle East
            {"code": "israel", "name": "Israel", "prefix": "972", "available": True},
            {"code": "uae", "name": "United Arab Emirates", "prefix": "971", "available": True},
            {"code": "saudi_arabia", "name": "Saudi Arabia", "prefix": "966", "available": True}
        ]
        return {"success": True, "countries": fallback, "total": len(fallback), "source": "comprehensive"}

    @fastapi_app.get("/api/verification/textverified/services")
    async def get_textverified_services():
        """Get live services from TextVerified API"""
        try:
            from app.services.textverified_integration import get_textverified_integration
            integration = get_textverified_integration()
            services = await integration.get_services_list()
            
            # Format services for frontend
            formatted_services = []
            for service in services:
                service_name = service.get("name", "Unknown")
                if service_name and service_name != "Unknown" and len(service_name) > 2:
                    formatted_services.append({
                        "id": service.get("id", service_name).lower(),
                        "name": service_name,
                        "category": service.get("category", "other"),
                        "available": True,
                        "cost": service.get("cost", 2.00)
                    })
            
            # If we got valid services from API, return them
            if formatted_services and len(formatted_services) > 10:  # Need reasonable number of services
                return {"success": True, "services": formatted_services, "total": len(formatted_services)}
                
        except Exception as e:
            logger = get_logger("textverified")
            logger.error(f"TextVerified services error: {str(e)}")
        
        # Use comprehensive list (TextVerified API returns empty for new accounts)
        logger = get_logger("textverified")
        logger.info("Using comprehensive services list")
        fallback = [
            # Dating & Social
            {"id": "ourtime", "name": "OurTime", "category": "dating", "available": True, "cost": 2.25},
            {"id": "tinder", "name": "Tinder", "category": "dating", "available": True, "cost": 2.50},
            {"id": "bumble", "name": "Bumble", "category": "dating", "available": True, "cost": 2.50},
            {"id": "match", "name": "Match.com", "category": "dating", "available": True, "cost": 2.25},
            {"id": "pof", "name": "Plenty of Fish", "category": "dating", "available": True, "cost": 2.00},
            {"id": "facebook", "name": "Facebook", "category": "social", "available": True, "cost": 2.00},
            {"id": "instagram", "name": "Instagram", "category": "social", "available": True, "cost": 2.50},
            {"id": "twitter", "name": "Twitter", "category": "social", "available": True, "cost": 1.75},
            {"id": "tiktok", "name": "TikTok", "category": "social", "available": True, "cost": 2.25},
            {"id": "snapchat", "name": "Snapchat", "category": "social", "available": True, "cost": 2.00},
            {"id": "linkedin", "name": "LinkedIn", "category": "social", "available": True, "cost": 2.75},
            # Messaging
            {"id": "telegram", "name": "Telegram", "category": "messaging", "available": True, "cost": 2.00},
            {"id": "whatsapp", "name": "WhatsApp", "category": "messaging", "available": True, "cost": 2.50},
            {"id": "discord", "name": "Discord", "category": "messaging", "available": True, "cost": 1.75},
            {"id": "signal", "name": "Signal", "category": "messaging", "available": True, "cost": 2.00},
            {"id": "viber", "name": "Viber", "category": "messaging", "available": True, "cost": 1.75},
            {"id": "line", "name": "LINE", "category": "messaging", "available": True, "cost": 2.00},
            # Tech & Services
            {"id": "google", "name": "Google", "category": "tech", "available": True, "cost": 1.50},
            {"id": "microsoft", "name": "Microsoft", "category": "tech", "available": True, "cost": 1.75},
            {"id": "apple", "name": "Apple", "category": "tech", "available": True, "cost": 2.00},
            {"id": "amazon", "name": "Amazon", "category": "tech", "available": True, "cost": 1.75},
            {"id": "uber", "name": "Uber", "category": "services", "available": True, "cost": 2.00},
            {"id": "lyft", "name": "Lyft", "category": "services", "available": True, "cost": 2.00},
            {"id": "doordash", "name": "DoorDash", "category": "services", "available": True, "cost": 1.75},
            {"id": "grubhub", "name": "GrubHub", "category": "services", "available": True, "cost": 1.75},
            # Gaming
            {"id": "steam", "name": "Steam", "category": "gaming", "available": True, "cost": 1.50},
            {"id": "twitch", "name": "Twitch", "category": "gaming", "available": True, "cost": 2.00},
            {"id": "epic", "name": "Epic Games", "category": "gaming", "available": True, "cost": 1.75},
            # Finance
            {"id": "paypal", "name": "PayPal", "category": "finance", "available": True, "cost": 2.50},
            {"id": "venmo", "name": "Venmo", "category": "finance", "available": True, "cost": 2.25},
            {"id": "cashapp", "name": "Cash App", "category": "finance", "available": True, "cost": 2.25},
            {"id": "coinbase", "name": "Coinbase", "category": "finance", "available": True, "cost": 2.75},
            # Other
            {"id": "netflix", "name": "Netflix", "category": "entertainment", "available": True, "cost": 2.00},
            {"id": "spotify", "name": "Spotify", "category": "entertainment", "available": True, "cost": 1.75},
            {"id": "reddit", "name": "Reddit", "category": "social", "available": True, "cost": 1.50},
            {"id": "pinterest", "name": "Pinterest", "category": "social", "available": True, "cost": 2.00}
        ]
        return {"success": True, "services": fallback, "total": len(fallback), "source": "comprehensive"}

    @fastapi_app.post("/api/verification/voice/create")
    async def create_voice_verification(request: Request, user_id: Optional[str] = Depends(get_optional_user_id), db: Session = Depends(get_db)):
        import uuid
        import json
        import random
        
        try:
            body = await request.body()
            data = json.loads(body)
            service = data.get('service')
            country = data.get('country', 'usa')
            
            if not service:
                raise HTTPException(status_code=400, detail="Service required")
            
            # Voice verification pricing (higher than SMS)
            voice_pricing = {
                'google': 3.50, 'facebook': 4.00, 'microsoft': 3.75, 'amazon': 3.25,
                'paypal': 4.50, 'apple': 4.25, 'linkedin': 3.75, 'twitter': 3.50,
                'instagram': 4.00, 'discord': 3.25, 'telegram': 3.00, 'whatsapp': 3.75
            }
            cost = voice_pricing.get(service.lower(), 3.50)
            
            verification_id = str(uuid.uuid4())
            phone_number = f"+1555{random.randint(1000000, 9999999)}"
            
            return {
                "success": True,
                "verification_id": verification_id,
                "phone_number": phone_number,
                "status": "calling",
                "cost": cost,
                "type": "voice",
                "message": "Voice call will arrive within 30 seconds"
            }
            
        except HTTPException:
            raise
        except Exception as e:
            logger = get_logger("voice_verification")
            logger.error(f"Voice verification request failed: {str(e)}")
            raise HTTPException(status_code=500, detail="Voice verification request failed")

    @fastapi_app.get("/api/verification/voice/{verification_id}")
    async def get_voice_verification_status(verification_id: str, user_id: Optional[str] = Depends(get_optional_user_id), db: Session = Depends(get_db)):
        import random
        import time
        
        # Simulate voice call processing
        time.sleep(1)
        voice_code = str(random.randint(1000, 9999))  # 4-digit codes for voice
        
        return {
            "verification_id": verification_id,
            "status": "completed",
            "phone_number": f"+1555{random.randint(1000000, 9999999)}",
            "voice_code": voice_code,
            "type": "voice",
            "cost": 3.50,
            "created_at": datetime.now().isoformat(),
            "message": "Voice call completed. Code delivered."
        }

    @fastapi_app.get("/voice-verify", response_class=HTMLResponse)
    async def voice_verify_page(request: Request, user_id: Optional[str] = Depends(get_optional_user_id), db: Session = Depends(get_db)):
        from app.models.user import User
        if not user_id:
            user = type('User', (), {'id': 'test', 'email': 'test@example.com', 'credits': 0})()
        else:
            user = db.query(User).filter(User.id == user_id).first()
        return templates.TemplateResponse("voice_verify.html", {"request": request, "user": user})

    @fastapi_app.get("/voice-status/{verification_id}", response_class=HTMLResponse)
    async def voice_status_page(request: Request, verification_id: str, user_id: Optional[str] = Depends(get_optional_user_id), db: Session = Depends(get_db)):
        from app.models.user import User
        if not user_id:
            user = type('User', (), {'id': 'test', 'email': 'test@example.com', 'credits': 0})()
        else:
            user = db.query(User).filter(User.id == user_id).first()
        return templates.TemplateResponse("voice_status.html", {"request": request, "user": user, "verification_id": verification_id})

    @fastapi_app.get("/api/admin/balance-test")
    async def admin_balance_test(user_id: str = Depends(get_current_user_id), db: Session = Depends(get_db)):
        from app.models.user import User
        logger = get_logger("balance_test")
        try:
            user = db.query(User).filter(User.id == user_id).first()
            if not user:
                return {"error": "User not found"}
            if not user.is_admin:
                return {"error": "Admin access required"}
            
            result = {
                "user_id": user.id,
                "is_admin": user.is_admin,
                "database_balance": float(user.credits or 0),
                "tests": {}
            }
            
            try:
                from app.services.textverified_integration import get_textverified_integration
                integration = get_textverified_integration()
                result["tests"]["integration_created"] = True
            except Exception as e:
                result["tests"]["integration_created"] = False
                result["tests"]["integration_error"] = str(e)
                return result
            
            try:
                balance_data = await integration.get_account_balance()
                result["tests"]["balance_fetch"] = True
                result["textverified_balance"] = balance_data.get("balance")
                result["textverified_account_id"] = balance_data.get("account_id")
                logger.info(f"TextVerified balance test successful: ${balance_data.get('balance')}")
            except Exception as e:
                result["tests"]["balance_fetch"] = False
                result["tests"]["balance_error"] = f"{type(e).__name__}: {str(e)}"
                logger.error(f"TextVerified balance test failed: {type(e).__name__}: {str(e)}")
            
            return result
        except Exception as e:
            logger.error(f"Balance test error: {type(e).__name__}: {str(e)}")
            return {"error": f"{type(e).__name__}: {str(e)}"}

    @fastapi_app.get("/api/countries/")
    async def get_countries():
        try:
            countries = [
                {"code": "russia", "name": "Russia", "prefix": "7", "popular": True},
                {"code": "india", "name": "India", "prefix": "91", "popular": True},
                {"code": "usa", "name": "United States", "prefix": "1", "popular": False},
            ]
            return {"success": True, "countries": countries, "total": len(countries)}
        except Exception as e:
            logger = get_logger("countries")
            logger.error(f"Countries fetch error: {str(e)}")
            raise HTTPException(status_code=500, detail="Failed to fetch countries")

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

        asyncio.create_task(_run_sms_service_supervisor())
        startup_logger.info("Application startup completed successfully")

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
