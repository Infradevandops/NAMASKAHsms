"""FastAPI dependencies for authentication and authorization."""

import jwt
from datetime import datetime, timezone
from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from app.core.config import get_settings
from app.core.database import get_db
from app.core.logging import get_logger
from app.models.user import User

logger = get_logger(__name__)
settings = get_settings()
security = HTTPBearer()


def get_current_user_id(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> str:
    """Extract and validate user ID from JWT token."""
    try:
        token = credentials.credentials
        payload = jwt.decode(
            token,
            settings.jwt_secret_key,
            algorithms=["HS256"]
        )
        
        user_id: str = payload.get("sub")
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Verify user exists
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        return user_id
        
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except jwt.JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )


def get_optional_user_id(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: Session = Depends(get_db)
) -> Optional[str]:
    """Extract user ID from JWT token if present, return None if not authenticated."""
    if not credentials:
        return None
    
    try:
        return get_current_user_id(credentials, db)
    except HTTPException:
        return None


def get_user_tier(user_id: str, db: Session) -> str:
    """Get user's current tier."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        return "freemium"
    return getattr(user, 'tier', 'freemium')


def has_tier_access(user_tier: str, required_tier: str) -> bool:
    """Check if user tier has access to required tier."""
    tier_hierarchy = {
        "freemium": 0,
        "payg": 1,
        "pro": 2,
        "custom": 3
    }
    
    user_level = tier_hierarchy.get(user_tier, 0)
    required_level = tier_hierarchy.get(required_tier, 0)
    
    return user_level >= required_level


def raise_tier_error(user_tier: str, required_tier: str, user_id: str = None):
    """Raise appropriate tier-related HTTP exception."""
    logger.warning(
        f"Tier access denied - user_id: {user_id}, user_tier: {user_tier}, required_tier: {required_tier}"
    )
    
    raise HTTPException(
        status_code=402,
        detail={
            "error": "insufficient_tier",
            "message": f"This feature requires {required_tier} tier or higher",
            "current_tier": user_tier,
            "required_tier": required_tier,
            "upgrade_url": "/billing/upgrade"
        }
    )


def require_tier(required_tier: str):
    """Create a dependency that requires a specific tier or higher.
    
    Args:
        required_tier: Minimum tier required ("freemium", "payg", "pro", "custom")
    
    Returns:
        FastAPI dependency function
    
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


# Common tier dependencies
require_payg = require_tier("payg")
require_pro = require_tier("pro")
require_custom = require_tier("custom")


def get_admin_user_id(
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
) -> str:
    """Require admin access and return user_id."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user or not user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    return user_id