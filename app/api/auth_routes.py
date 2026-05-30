"""
Consolidated Authentication System - Single Source of Truth
"""

import asyncio
from datetime import datetime, timedelta, timezone
from typing import Optional

import bcrypt
import jwt
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.database import get_db
from app.core.dependencies import get_current_user_id
from app.core.logging import get_logger
from app.models.user import User

logger = get_logger(__name__)
router = APIRouter(prefix="/api/auth", tags=["Authentication"])
security = HTTPBearer()
settings = get_settings()


class LoginRequest(BaseModel):
    """Login request model."""

    email: EmailStr
    password: str
    mfa_token: Optional[str] = None
    turnstile_token: Optional[str] = None


class RegisterRequest(BaseModel):
    """Register request model."""

    email: EmailStr
    password: str
    username: Optional[str] = None
    terms_accepted: bool = False
    turnstile_token: Optional[str] = None


class OnboardingStatusUpdateRequest(BaseModel):
    """Onboarding status update request model."""

    step: int


class TokenResponse(BaseModel):
    """Token response model."""

    access_token: str
    refresh_token: Optional[str] = None
    token_type: str = "bearer"
    user: dict
    redirect: Optional[str] = None


@router.post("/login", response_model=TokenResponse)
async def login(login_data: LoginRequest, db: Session = Depends(get_db)):
    """Login endpoint - consolidated and working."""
    # Verify Turnstile token
    from app.core.turnstile import verify_turnstile

    if not await verify_turnstile(login_data.turnstile_token):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Bot verification failed. Please try again.",
        )

    try:
        # Find user by email
        user = db.query(User).filter(User.email == login_data.email).first()

        if not user:
            logger.warning(f"Login attempt with non-existent email: {login_data.email}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password",
            )

        # Verify password
        if not user.password_hash:
            logger.error(f"User {user.email} has no password hash")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password",
            )

        try:
            password_match = bcrypt.checkpw(
                login_data.password.encode("utf-8"), user.password_hash.encode("utf-8")
            )
        except (ValueError, Exception) as e:
            logger.warning(f"Password verification error for {user.email}: {e}")
            password_match = False

        if not password_match:
            logger.warning(f"Invalid password for user: {user.email}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password",
            )

        # Check if user is active
        if not user.is_active:
            logger.warning(f"Login attempt for inactive user: {user.email}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="Account is disabled"
            )

        # MFA check
        if getattr(user, "mfa_enabled", False):
            if not login_data.mfa_token:
                return {
                    "access_token": "",
                    "token_type": "bearer",
                    "mfa_required": True,
                    "user": {"email": user.email},
                }
            from app.services.mfa_service import MFAService

            if not MFAService.verify_token(user.mfa_secret, login_data.mfa_token):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid MFA token",
                )
        import uuid

        token_data = {
            "user_id": str(user.id),
            "email": user.email,
            "iat": datetime.now(timezone.utc),
            "jti": str(uuid.uuid4()),
            "exp": datetime.now(timezone.utc)
            + timedelta(hours=settings.jwt_expiration_hours),
        }

        access_token = jwt.encode(
            token_data, settings.jwt_secret_key, algorithm=settings.jwt_algorithm
        )

        # Generate refresh token
        refresh_token_data = {
            "user_id": str(user.id),
            "email": user.email,
            "iat": datetime.now(timezone.utc),
            "jti": str(uuid.uuid4()),
            "exp": datetime.now(timezone.utc) + timedelta(days=30),
            "type": "refresh",
        }
        refresh_token = jwt.encode(
            refresh_token_data,
            settings.jwt_secret_key,
            algorithm=settings.jwt_algorithm,
        )

        # Update last login
        user.last_login = datetime.now(timezone.utc)
        db.commit()

        logger.info(f"Successful login: {user.email}")

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "user": {
                "id": str(user.id),
                "email": user.email,
                "username": user.email.split("@")[0],
                "credits": float(user.credits) if user.credits else 0.0,
                "is_active": user.is_active,
                "is_admin": user.is_admin,
            },
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Login failed"
        )


@router.post("/register", response_model=TokenResponse)
async def register(register_data: RegisterRequest, db: Session = Depends(get_db)):
    """Register endpoint - consolidated and working."""
    # Verify Turnstile token
    from app.core.turnstile import verify_turnstile

    if not await verify_turnstile(register_data.turnstile_token):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Bot verification failed. Please try again.",
        )

    try:
        # Check if user already exists
        existing_user = db.query(User).filter(User.email == register_data.email).first()

        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered",
            )

        # Hash password
        password_hash = bcrypt.hashpw(
            register_data.password.encode("utf-8"), bcrypt.gensalt()
        ).decode("utf-8")

        # Validate terms acceptance
        if not register_data.terms_accepted:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="You must accept the Terms of Service and Privacy Policy",
            )

        # Create user
        user = User(
            email=register_data.email,
            password_hash=password_hash,
            is_active=True,
            credits=0.0,
            terms_accepted=True,
            terms_accepted_at=datetime.now(timezone.utc),
        )

        db.add(user)
        db.commit()
        db.refresh(user)

        # Send verification + welcome emails (non-blocking)
        try:
            import uuid

            from app.services.email_service import email_service

            verification_token = uuid.uuid4().hex
            user.verification_token = verification_token
            db.commit()
            base_url = (
                settings.base_url
                if hasattr(settings, "base_url") and settings.base_url
                else "https://vrenum.app"
            )
            display_name = user.email.split("@")[0]
            asyncio.create_task(
                email_service.send_verification_email(
                    user.email, verification_token, base_url
                )
            )
            asyncio.create_task(
                email_service.send_welcome_email(
                    user.email, user_name=display_name, base_url=base_url
                )
            )
        except Exception as email_err:
            logger.warning(f"Registration emails failed for {user.email}: {email_err}")

        # Generate JWT token
        token_data = {
            "user_id": str(user.id),
            "email": user.email,
            "exp": datetime.now(timezone.utc)
            + timedelta(hours=settings.jwt_expiration_hours),
        }

        access_token = jwt.encode(
            token_data, settings.jwt_secret_key, algorithm=settings.jwt_algorithm
        )

        logger.info(f"New user registered: {user.email}")

        return {
            "access_token": access_token,
            "token_type": "bearer",
            "redirect": "/welcome",
            "user": {
                "id": str(user.id),
                "email": user.email,
                "username": user.email.split("@")[0],
                "credits": 0.0,
                "is_active": True,
            },
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Registration error: {str(e)}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Registration failed",
        )


@router.get("/me")
async def get_current_user(
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Get current user info."""
    try:
        # Get user
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
            )

        return {
            "id": str(user.id),
            "email": user.email,
            "username": user.email.split("@")[0],
            "credits": float(user.credits) if user.credits else 0.0,
            "tier": getattr(user, "subscription_tier", "freemium") or "freemium",
            "free_verifications": (
                int(user.free_verifications)
                if hasattr(user, "free_verifications") and user.free_verifications
                else 0
            ),
            "is_active": user.is_active,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get user error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get user info",
        )


@router.post("/logout")
async def logout(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
):
    """Logout endpoint — revokes the JWT so it cannot be reused."""
    from app.services.auth_service import AuthService

    auth_service = AuthService(db)
    auth_service.revoke_token(credentials.credentials)
    return {"message": "Successfully logged out"}


def _get_user_from_token(token: str, db: Session) -> User:
    """Decode JWT and return the User, raising 401/404 on failure."""
    try:
        payload = jwt.decode(token, settings.jwt_secret_key, algorithms=["HS256"])
        user_id = payload.get("user_id")
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token"
            )
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Token expired"
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token"
        )
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )
    return user


@router.get("/onboarding-status")
async def get_onboarding_status(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
):
    """Return current onboarding progress for the authenticated user."""
    user = _get_user_from_token(credentials.credentials, db)
    return {
        "completed": bool(user.onboarding_completed),
        "step": int(user.onboarding_step or 0),
    }


@router.put("/onboarding-status")
async def update_onboarding_status(
    data: OnboardingStatusUpdateRequest,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
):
    """Update current onboarding step for the authenticated user."""
    user = _get_user_from_token(credentials.credentials, db)
    user.onboarding_step = data.step
    db.commit()
    return {"status": "success", "step": user.onboarding_step}


@router.put("/onboarding-complete")
async def complete_onboarding(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
):
    """Mark onboarding as complete (idempotent)."""
    user = _get_user_from_token(credentials.credentials, db)
    user.onboarding_completed = True
    user.onboarding_step = 6
    db.commit()
    return {"status": "completed"}
