"""FastAPI dependency injection utilities."""


import logging
from typing import Callable, Optional
import jwt
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session
from app.models.user import User
from .config import settings
from .database import get_db
from .tier_helpers import get_user_tier, has_tier_access, raise_tier_error
from app.models.user import User

logger = logging.getLogger(__name__)

security = HTTPBearer(auto_error=False)


def get_token_from_request(request: Request, credentials: HTTPAuthorizationCredentials = Depends(security)) -> str:
    """Extract token from Authorization header or cookies."""
    if credentials:
        return credentials.credentials

    token = request.cookies.get("access_token")
    if token:
        return token

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Not authenticated",
        headers={"WWW-Authenticate": "Bearer"},
    )


def get_current_user_id(
    token: str = Depends(get_token_from_request),
) -> str:
    """Get current user ID from JWT token."""
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm],
        )
        user_id = payload.get("user_id")
        if not user_id:
            logger.warning("Token missing user_id")
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
        return user_id
    except jwt.InvalidTokenError as e:
        logger.warning(f"Token decode failed: {str(e)}")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")


def get_current_user(user_id: str = Depends(get_current_user_id), db: Session = Depends(get_db)):
    """Get current user object from database."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return user


def get_admin_user_id(user_id: str = Depends(get_current_user_id), db: Session = Depends(get_db)) -> str:
    """Get admin user ID (requires admin role)."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user or not user.is_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")
    return user_id


def get_current_admin_user(user_id: str = Depends(get_current_user_id), db: Session = Depends(get_db)):
    """Get current admin user object (requires admin role)."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user or not user.is_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")
    return user


def get_optional_user_id(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> Optional[str]:
    """Get user ID from JWT token if provided, otherwise return None."""
    if not credentials:
        return None
    try:
        payload = jwt.decode(
            credentials.credentials,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm],
        )
        return payload.get("user_id")
    except jwt.InvalidTokenError:
        return None


def require_tier(required_tier: str) -> Callable:
    """Factory function to create tier requirement dependencies.

    Creates a FastAPI dependency that validates the current user's tier
    against the required tier level.

    Args:
        required_tier: The minimum tier required (freemium, payg, pro, custom)

    Returns:
        A dependency function that validates tier and returns user_id

    Raises:
        HTTPException: 402 Payment Required if user's tier is insufficient
    """

def tier_dependency(user_id: str = Depends(get_current_user_id), db: Session = Depends(get_db)) -> str:
        """Validate user tier and return user_id if authorized."""
        user_tier = get_user_tier(user_id, db)

        if not has_tier_access(user_tier, required_tier):
            raise_tier_error(user_tier, required_tier, user_id)

        logger.debug(
            f"Tier access granted - user_id: {user_id}, user_tier: {user_tier}, required_tier: {required_tier}"
        )
        return user_id

    return tier_dependency