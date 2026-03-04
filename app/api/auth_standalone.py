"""Standalone auth endpoints - temporary solution while core_router is disabled."""

from datetime import datetime, timedelta, timezone
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session
import bcrypt
import jwt

from app.core.config import get_settings
from app.core.database import get_db
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


class RegisterRequest(BaseModel):
    """Register request model."""
    email: EmailStr
    password: str
    username: Optional[str] = None


class TokenResponse(BaseModel):
    """Token response model."""
    access_token: str
    token_type: str = "bearer"
    user: dict


@router.post("/login", response_model=TokenResponse)
async def login(login_data: LoginRequest, db: Session = Depends(get_db)):
    """Login endpoint."""
    try:
        user = db.query(User).filter(User.email == login_data.email).first()

        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password"
            )

        if not bcrypt.checkpw(
            login_data.password.encode('utf-8'),
            user.password_hash.encode('utf-8')
        ):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password"
            )

        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Account is disabled"
            )

        token_data = {
            "user_id": str(user.id),
            "email": user.email,
            "exp": datetime.now(timezone.utc) + timedelta(days=7)
        }

        access_token = jwt.encode(
            token_data,
            settings.jwt_secret_key,
            algorithm=settings.jwt_algorithm
        )

        user.last_login = datetime.now(timezone.utc)
        db.commit()

        logger.info(f"User logged in: {user.email}")

        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user": {
                "id": str(user.id),
                "email": user.email,
                "username": user.username,
                "credits": float(user.credits) if user.credits else 0.0,
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Login failed"
        )


@router.post("/register", response_model=TokenResponse)
async def register(register_data: RegisterRequest, db: Session = Depends(get_db)):
    """Register endpoint."""
    try:
        existing_user = db.query(User).filter(User.email == register_data.email).first()

        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )

        password_hash = bcrypt.hashpw(
            register_data.password.encode('utf-8'),
            bcrypt.gensalt()
        ).decode('utf-8')

        user = User(
            email=register_data.email,
            username=register_data.username or register_data.email.split('@')[0],
            password_hash=password_hash,
            is_active=True,
            credits=0.0,
            created_at=datetime.now(timezone.utc)
        )

        db.add(user)
        db.commit()
        db.refresh(user)

        token_data = {
            "user_id": str(user.id),
            "email": user.email,
            "exp": datetime.now(timezone.utc) + timedelta(days=7)
        }

        access_token = jwt.encode(
            token_data,
            settings.jwt_secret_key,
            algorithm=settings.jwt_algorithm
        )

        logger.info(f"New user registered: {user.email}")

        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user": {
                "id": str(user.id),
                "email": user.email,
                "username": user.username,
                "credits": 0.0,
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Registration error: {str(e)}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Registration failed"
        )


@router.get("/me")
async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    """Get current user info."""
    try:
        payload = jwt.decode(
            credentials.credentials,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm]
        )

        user_id = payload.get("user_id")
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token"
            )

        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )

        return {
            "id": str(user.id),
            "email": user.email,
            "username": user.username,
            "credits": float(user.credits) if user.credits else 0.0,
            "is_active": user.is_active,
        }

    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token expired"
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )
    except Exception as e:
        logger.error(f"Get user error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get user info"
        )
