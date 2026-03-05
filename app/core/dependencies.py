"""FastAPI dependencies for authentication and authorization."""

from typing import Optional
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.logging import get_logger
from app.models.user import User
from app.services.auth_service import AuthService

logger = get_logger(__name__)
security = HTTPBearer(auto_error=False)


def get_current_user_id(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: Session = Depends(get_db)
) -> str:
    """Get current user ID from JWT token (header or cookie)."""
    token = None
    
    # Try Authorization header first
    if credentials:
        token = credentials.credentials
    # Fall back to cookie
    elif "access_token" in request.cookies:
        token = request.cookies["access_token"]
    
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated"
        )
    
    try:
        auth_service = AuthService(db)
        user_id = auth_service.verify_token(token)
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials"
            )
        return user_id
    except Exception as e:
        logger.error(f"Authentication error: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials"
        )


def get_current_user(
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
) -> User:
    """Get current user object."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    return user


def get_admin_user_id(
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
) -> str:
    """Verify user is admin and return user ID."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    if not user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    return user_id


def get_optional_user_id(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: Session = Depends(get_db)
) -> Optional[str]:
    """Get user ID if authenticated, None otherwise."""
    token = None
    
    if credentials:
        token = credentials.credentials
    elif "access_token" in request.cookies:
        token = request.cookies["access_token"]
    
    if not token:
        return None
    
    try:
        auth_service = AuthService(db)
        return auth_service.verify_token(token)
    except:
        return None


def require_tier(required_tier: str):
    """Create a dependency that requires a specific tier."""
    def tier_dependency(
        user_id: str = Depends(get_current_user_id),
        db: Session = Depends(get_db)
    ) -> str:
        """Validate user tier and return user_id if authorized."""
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Simple tier check - you can expand this logic
        user_tier = getattr(user, 'subscription_tier', 'freemium')
        
        tier_hierarchy = ['freemium', 'payg', 'pro', 'custom']
        required_level = tier_hierarchy.index(required_tier) if required_tier in tier_hierarchy else 0
        user_level = tier_hierarchy.index(user_tier) if user_tier in tier_hierarchy else 0
        
        if user_level < required_level:
            raise HTTPException(
                status_code=status.HTTP_402_PAYMENT_REQUIRED,
                detail=f"Tier '{required_tier}' required. Current tier: '{user_tier}'"
            )
        
        return user_id
    
    return tier_dependency


# Common tier dependencies
require_payg = require_tier("payg")
require_pro = require_tier("pro")
require_custom = require_tier("custom")


def require_payment_method(
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
) -> str:
    """Block access if no card on file and balance is below $1."""
    from app.models.user_preference import UserPreference
    from app.models.user import User as _User
    user = db.query(_User).filter(_User.id == user_id).first()
    pref = db.query(UserPreference).filter(UserPreference.user_id == user_id).first()
    has_card = bool(pref and pref.paystack_authorization_code)
    balance = float(user.credits or 0) if user else 0.0
    if not has_card and balance < 1.0:
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail="A saved payment method or minimum $1.00 balance is required for API access.",
        )
    return user_id