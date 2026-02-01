"""Authentication API router."""

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import (  # Keep JSONResponse and HTMLResponse as they are used later
from google.oauth2 import id_token  # Keep id_token as it might be used for Google OAuth
from pydantic import BaseModel  # Added back BaseModel as it's used by SuccessResponse
from sqlalchemy.orm import Session
from app.core.auth_security import audit_log_auth_event, record_login_attempt
from app.core.config import get_settings
from app.core.database import get_db
from app.core.dependencies import get_current_user_id, require_tier
from app.core.exceptions import AuthenticationError, ValidationError
from app.core.token_manager import create_tokens
from app.models.api_key import APIKey
from app.models.user import User
from app.schemas.auth import (
from app.services import get_auth_service, get_notification_service
import secrets
from app.models.user import User
from app.utils.security import verify_password
import traceback
from datetime import datetime, timezone
from app.core.token_manager import get_refresh_token_expiry
from google.auth.transport import requests as google_requests
from app.core.token_manager import verify_refresh_token
from datetime import datetime, timezone
from app.core.token_manager import get_refresh_token_expiry
from app.core.logging import get_logger

    HTMLResponse,
    JSONResponse,
)

    APIKeyCreate,
    APIKeyListResponse,
    APIKeyResponse,
    GoogleAuthRequest,
    LoginRequest,
    PasswordResetConfirm,
    PasswordResetRequest,
    TokenResponse,
    UserCreate,
    UserResponse,
)


class SuccessResponse(BaseModel):

    message: str


router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(user_data: UserCreate, request: Request, db: Session = Depends(get_db)):
    """Register new user account."""

    auth_service = get_auth_service(db)
    notification_service = get_notification_service(db)
    ip_address = request.client.host if request.client else "unknown"
    user_agent = request.headers.get("user-agent", "unknown")

try:
        new_user = auth_service.register_user(
            email=user_data.email,
            password=user_data.password,
            referral_code=getattr(user_data, "referral_code", None),
        )

        tokens = create_tokens(new_user.id, new_user.email)

try:
            audit_log_auth_event(
                db,
                "register",
                user_id=new_user.id,
                ip_address=ip_address,
                user_agent=user_agent,
            )
except Exception:
            pass

        # Generate verification token

        verification_token = secrets.token_urlsafe(32)
        new_user.verification_token = verification_token
        db.commit()

        # Send verification email
        await notification_service.send_email(
            to_email=new_user.email,
            subject="Verify Your Email - Namaskah SMS",
            body="<h2>Welcome to Namaskah SMS!</h2>"
            + "<p>Please verify your email to activate your account.</p>"
            + f"<p><a href='http://127.0.0.1:8000/api/auth/verify-email?token={verification_token}'>Verify Email</a></p>"
            + "<p>This link expires in 24 hours.</p>",
        )

        user_dict = UserResponse.model_validate(new_user).model_dump()
        user_dict["created_at"] = (
            user_dict["created_at"].isoformat()
if hasattr(user_dict["created_at"], "isoformat")
            else str(user_dict["created_at"])
        )

        response = JSONResponse(
            status_code=status.HTTP_201_CREATED,
            content={
                "access_token": tokens["access_token"],
                "token_type": tokens["token_type"],
                "user": user_dict,
            },
        )

        response.set_cookie(
            "access_token",
            tokens["access_token"],
            httponly=True,
            secure=True,
            samesite="strict",
            max_age=900,
        )
        response.set_cookie(
            "refresh_token",
            tokens["refresh_token"],
            httponly=True,
            secure=True,
            samesite="strict",
            max_age=2592000,
        )

        return response

except ValidationError:
try:
            audit_log_auth_event(db, "register_failed", ip_address=ip_address, user_agent=user_agent)
except Exception:
            pass
        raise HTTPException(status_code=400, detail="Registration validation failed")
except (ValueError, KeyError, AttributeError):
try:
            audit_log_auth_event(db, "register_failed", ip_address=ip_address, user_agent=user_agent)
except Exception:
            pass
        raise HTTPException(status_code=400, detail="Invalid registration data")


@router.get("/google/config")
def get_google_config():

    """Serve Google OAuth config."""
    settings = get_settings()
    return JSONResponse(
        content={
            "client_id": settings.google_client_id
            or "11893866195-r9q595mc77j5n2c0j1neki1lmr3es3fb.apps.googleusercontent.com",
            "features": {
                "websocket_enabled": True,
                "real_time_updates": True,
                "bulk_verification": True,
                "enhanced_security": True,
            },
        }
    )


@router.get("/login", response_class=HTMLResponse)
async def login_page():
    """Login page."""
with open("templates/login.html", "r") as f:
        return f.read()


@router.post("/login", response_model=TokenResponse)
async def login(login_data: LoginRequest, request: Request, db: Session = Depends(get_db)):
    """Authenticate user with email and password."""

    print(f"[DEBUG] LOGIN ATTEMPT: email={login_data.email}, password_len={len(login_data.password)}")
    print(f"[DEBUG] Password starts with: {login_data.password[:3]}...")
    print(f"[DEBUG] Request headers: {dict(request.headers)}")
    ip_address = request.client.host if request.client else "unknown"
    user_agent = request.headers.get("user-agent", "unknown")

try:
        # Direct authentication without service layer to avoid session issues

try:
            user = db.query(User).filter(User.email == login_data.email).first()
            print(f"[DEBUG] User found: {user is not None}")
if user:
                print(f"[DEBUG] User ID: {user.id}")
                print(f"[DEBUG] User email: {user.email}")
                print(f"[DEBUG] Has password_hash: {bool(user.password_hash)}")
                print(f"[DEBUG] Email verified: {user.email_verified}")
if user.password_hash:
                    verified = verify_password(login_data.password, user.password_hash)
                    print(f"[DEBUG] Password verified: {verified}")
                    print(f"[DEBUG] Hash starts with: {user.password_hash[:20]}...")
except Exception as e:
            print(f"[DEBUG] Exception during auth: {e}")

            traceback.print_exc()
            user = None
            verified = False

if not user or not user.password_hash or not verify_password(login_data.password, user.password_hash):
try:
                record_login_attempt(db, login_data.email, ip_address, False)
except Exception:
                pass
try:
                audit_log_auth_event(db, "login_failed", ip_address=ip_address, user_agent=user_agent)
except Exception:
                pass
            raise HTTPException(status_code=401, detail="Invalid email or password")

        authenticated_user = user

if not authenticated_user:
            record_login_attempt(db, login_data.email, ip_address, False)
try:
                audit_log_auth_event(db, "login_failed", ip_address=ip_address, user_agent=user_agent)
except Exception:
                pass
            raise HTTPException(status_code=401, detail="Invalid email or password")

        record_login_attempt(db, login_data.email, ip_address, True)
try:
            audit_log_auth_event(
                db,
                "login",
                user_id=authenticated_user.id,
                ip_address=ip_address,
                user_agent=user_agent,
            )
except Exception:
            pass

        # Task 1.2: Create tokens and store refresh token


        tokens = create_tokens(authenticated_user.id, authenticated_user.email)

        # Store refresh token in database
        authenticated_user.refresh_token = tokens["refresh_token"]
        authenticated_user.refresh_token_expires = get_refresh_token_expiry()
        authenticated_user.last_login = datetime.now(timezone.utc)
        db.commit()

        response = JSONResponse(
            content={
                "access_token": tokens["access_token"],
                "refresh_token": tokens["refresh_token"],
                "token_type": tokens["token_type"],
                "expires_in": tokens["expires_in"],
                "user": {
                    "id": authenticated_user.id,
                    "email": authenticated_user.email,
                    "is_admin": authenticated_user.is_admin,
                },
            }
        )

        response.set_cookie(
            "access_token",
            tokens["access_token"],
            httponly=True,
            secure=True,
            samesite="strict",
            max_age=86400,
        )
        response.set_cookie(
            "refresh_token",
            tokens["refresh_token"],
            httponly=True,
            secure=True,
            samesite="strict",
            max_age=2592000,
        )

        return response

except HTTPException:
        raise
except AuthenticationError:
try:
            audit_log_auth_event(db, "login_failed", ip_address=ip_address, user_agent=user_agent)
except Exception:
            pass
        raise HTTPException(status_code=401, detail="Authentication failed")
except (ValueError, KeyError):
try:
            audit_log_auth_event(db, "login_error", ip_address=ip_address, user_agent=user_agent)
except Exception:
            pass
        raise HTTPException(status_code=401, detail="Invalid email or password")


@router.post("/google", response_model=TokenResponse)
async def google_auth(google_data: GoogleAuthRequest, request: Request, db: Session = Depends(get_db)):
    """Authenticate with Google OAuth."""
    ip_address = request.client.host if request.client else "unknown"
    user_agent = request.headers.get("user-agent", "unknown")

try:

        settings = get_settings()
        auth_service = get_auth_service(db)

        idinfo = id_token.verify_oauth2_token(google_data.token, google_requests.Request(), settings.google_client_id)

        google_id = idinfo["sub"]
        email = idinfo["email"]
        name = idinfo.get("name", "")
        avatar_url = idinfo.get("picture")

        user = auth_service.create_or_get_google_user(
            google_id=google_id, email=email, name=name, avatar_url=avatar_url
        )

try:
            audit_log_auth_event(
                db,
                "google_login",
                user_id=user.id,
                ip_address=ip_address,
                user_agent=user_agent,
            )
except Exception:
            pass
        access_token = auth_service.create_user_token(user)

        return TokenResponse(
            access_token=access_token,
            token_type="bearer",
            user=UserResponse.model_validate(user),
        )

except ValueError:
try:
            audit_log_auth_event(db, "google_login_failed", ip_address=ip_address, user_agent=user_agent)
except Exception:
            pass
        raise HTTPException(status_code=401, detail="Invalid Google token")
except (KeyError, AttributeError):
try:
            audit_log_auth_event(db, "google_login_error", ip_address=ip_address, user_agent=user_agent)
except Exception:
            pass
        raise HTTPException(status_code=401, detail="Google authentication failed")


@router.get("/me", response_model=UserResponse)
def get_current_user(user_id: str = Depends(get_current_user_id), db: Session = Depends(get_db)):

    """Get current authenticated user information."""
    current_user = db.query(User).filter(User.id == user_id).first()

if not current_user:
        raise HTTPException(status_code=404, detail="User not found")

    response = UserResponse.model_validate(current_user)
    response.credits = current_user.credits
    response.free_verifications = current_user.free_verifications
    return response


@router.post("/forgot-password", response_model=SuccessResponse)
async def forgot_password(request_data: PasswordResetRequest, db: Session = Depends(get_db)):
    """Request password reset link."""
    auth_service = get_auth_service(db)
    notification_service = get_notification_service(db)

    reset_token = auth_service.reset_password_request(request_data.email)

if reset_token:
        await notification_service.send_email(
            to_email=request_data.email,
            subject="Password Reset - Namaskah SMS",
            body="<h2>Password Reset Request</h2>"
            + "<p>Click the link below to reset your password:</p>"
            + f"<p><a href='/auth/reset-password?token={reset_token}'>Reset Password</a></p>"
            + "<p>This link expires in 1 hour.</p>",
        )

    return SuccessResponse(message="If email exists, reset link sent")


@router.post("/reset-password", response_model=SuccessResponse)
def reset_password(reset_data: PasswordResetConfirm, db: Session = Depends(get_db)):

    """Reset password using token."""
    auth_service = get_auth_service(db)

    success = auth_service.reset_password(reset_data.token, reset_data.new_password)

if not success:
        raise HTTPException(status_code=400, detail="Invalid or expired reset token")

    return SuccessResponse(message="Password reset successfully")


@router.get("/verify-email", response_model=SuccessResponse)
def verify_email(token: str, db: Session = Depends(get_db)):

    """Verify email address using token."""
    user = db.query(User).filter(User.verification_token == token).first()

if not user:
        raise HTTPException(status_code=400, detail="Invalid verification token")

    user.email_verified = True
    user.verification_token = None
    db.commit()

    return SuccessResponse(message="Email verified successfully. You can now use all features.")


# Tier dependency for payg+ access to API keys
require_payg_for_api_keys = require_tier("payg")


@router.post("/api-keys", response_model=APIKeyResponse, status_code=status.HTTP_201_CREATED)
def create_api_key(

    api_key_data: APIKeyCreate,
    user_id: str = Depends(require_payg_for_api_keys),
    db: Session = Depends(get_db),
):
    """Create new API key for programmatic access. Requires PayG tier or higher."""
    user = db.query(User).filter(User.id == user_id).first()
if not user or not user.email_verified:
        raise HTTPException(status_code=403, detail="Email verification required")
    auth_service = get_auth_service(db)
    api_key = auth_service.create_api_key(user_id, api_key_data.name)
    return {
        "id": api_key.id,
        "name": api_key.name,
        "key": api_key.raw_key,
        "is_active": api_key.is_active,
        "created_at": api_key.created_at,
        "last_used": api_key.last_used,
    }


@router.get("/api-keys", response_model=list[APIKeyListResponse])
def list_api_keys(user_id: str = Depends(require_payg_for_api_keys), db: Session = Depends(get_db)):

    """List user's API keys. Requires PayG tier or higher."""

    api_keys = db.query(APIKey).filter(APIKey.user_id == user_id).all()

    return [
        APIKeyListResponse(
            id=key.id,
            name=key.name,
            key_preview=key.key_preview,
            is_active=key.is_active,
            created_at=key.created_at,
            last_used=key.last_used,
        )
for key in api_keys
    ]


@router.delete("/api-keys/{key_id}", response_model=SuccessResponse)
def delete_api_key(

    key_id: str,
    user_id: str = Depends(require_payg_for_api_keys),
    db: Session = Depends(get_db),
):
    """Delete API key. Requires PayG tier or higher."""

    api_key = db.query(APIKey).filter(APIKey.id == key_id, APIKey.user_id == user_id).first()

if not api_key:
        raise HTTPException(status_code=404, detail="API key not found")

    db.delete(api_key)
    db.commit()

    return SuccessResponse(message="API key deleted successfully")


@router.post("/logout", response_model=SuccessResponse)
def logout(

    user_id: str = Depends(get_current_user_id),
    request: Request = None,
    db: Session = Depends(get_db),
):
    """Logout user."""
    ip_address = request.client.host if request and request.client else "unknown"
    user_agent = request.headers.get("user-agent", "unknown") if request else "unknown"
try:
        audit_log_auth_event(db, "logout", user_id=user_id, ip_address=ip_address, user_agent=user_agent)
except Exception:
        pass
    return SuccessResponse(message="Logged out successfully")


@router.post("/refresh", response_model=TokenResponse)
async def refresh_access_token(request: Request, db: Session = Depends(get_db)):
    """Refresh access token using refresh token."""
try:
        # Try to get refresh token from multiple sources
        refresh_token = None

        # 1. Check request body
try:
            body = await request.json()
            refresh_token = body.get("refresh_token")
except Exception:
            pass

        # 2. Check cookies
if not refresh_token:
            refresh_token = request.cookies.get("refresh_token")

        # 3. Check Authorization header
if not refresh_token:
            auth_header = request.headers.get("Authorization", "")
if auth_header.startswith("Bearer "):
                refresh_token = auth_header[7:]

if not refresh_token:
            raise HTTPException(status_code=401, detail="Refresh token missing")

        # Verify and decode refresh token

        payload = verify_refresh_token(refresh_token)

if not payload:
            raise HTTPException(status_code=401, detail="Invalid refresh token")

        user_id = payload.get("sub")
if not user_id:
            raise HTTPException(status_code=401, detail="Invalid token payload")

        # Get user from database
        user = db.query(User).filter(User.id == user_id).first()
if not user:
            raise HTTPException(status_code=404, detail="User not found")

        # Verify stored refresh token matches
if user.refresh_token != refresh_token:
            raise HTTPException(status_code=401, detail="Token mismatch")

        # Check if refresh token is expired

if user.refresh_token_expires and user.refresh_token_expires < datetime.now(timezone.utc):
            raise HTTPException(status_code=401, detail="Refresh token expired")

        # Create new tokens
        tokens = create_tokens(user.id, user.email)

        # Update stored refresh token

        user.refresh_token = tokens["refresh_token"]
        user.refresh_token_expires = get_refresh_token_expiry()
        db.commit()

        response = JSONResponse(
            content={
                "access_token": tokens["access_token"],
                "refresh_token": tokens["refresh_token"],
                "token_type": tokens["token_type"],
                "expires_in": tokens["expires_in"],
            }
        )

        # Set cookies
        response.set_cookie(
            "access_token",
            tokens["access_token"],
            httponly=True,
            secure=True,
            samesite="strict",
            max_age=86400,
        )
        response.set_cookie(
            "refresh_token",
            tokens["refresh_token"],
            httponly=True,
            secure=True,
            samesite="strict",
            max_age=2592000,
        )

        return response

except HTTPException:
        raise
except Exception as e:

        logger = get_logger(__name__)
        logger.error(f"Token refresh error: {e}")
        raise HTTPException(status_code=401, detail="Token refresh failed")