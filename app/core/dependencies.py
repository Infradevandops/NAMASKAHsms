"""FastAPI dependencies for authentication and authorization."""

from typing import Optional

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.logging import get_logger
from app.models.user import User
# AuthService import moved inside functions to avoid circular dependency
from app.services.tier_manager import TierManager

logger = get_logger(__name__)
security = HTTPBearer(auto_error=False)


def get_current_user_id(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: Session = Depends(get_db),
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
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated"
        )

    try:
        from app.services.auth_service import AuthService
        auth_service = AuthService(db)
        user_id = auth_service.verify_token(token)
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials",
            )
        return user_id
    except Exception as e:
        logger.error(f"Authentication error: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
        )


def get_current_user(
    user_id: str = Depends(get_current_user_id), db: Session = Depends(get_db)
) -> User:
    """Get current user object."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )
    return user


def get_admin_user_id(
    user_id: str = Depends(get_current_user_id), db: Session = Depends(get_db)
) -> str:
    """Verify user is admin and return user ID."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )

    if not user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required"
        )

    return user_id


def get_optional_user_id(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: Session = Depends(get_db),
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
        from app.services.auth_service import AuthService
        auth_service = AuthService(db)
        return auth_service.verify_token(token)
    except Exception as e:
        logger.warning("Token verification failed", extra={"error": str(e)})
        return None


def require_tier(required_tier: str):
    """Create a dependency that requires a specific tier."""

    def tier_dependency(
        user_id: str = Depends(get_current_user_id), db: Session = Depends(get_db)
    ) -> str:
        """Validate user tier and return user_id if authorized."""
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
            )

        # Admins always pass any tier gate
        if getattr(user, "is_admin", False):
            return user_id

        # Use TierManager to get the live, expiry-checked tier
        user_tier = TierManager(db).get_user_tier(user_id)

        tier_hierarchy = ["freemium", "payg", "pro", "custom"]
        required_level = (
            tier_hierarchy.index(required_tier)
            if required_tier in tier_hierarchy
            else 0
        )
        user_level = (
            tier_hierarchy.index(user_tier) if user_tier in tier_hierarchy else 0
        )

        if user_level < required_level:
            raise HTTPException(
                status_code=status.HTTP_402_PAYMENT_REQUIRED,
                detail=f"Tier '{required_tier}' required. Current tier: '{user_tier}'",
            )

        return user_id

    return tier_dependency


# Common tier dependencies
require_payg = require_tier("payg")
require_pro = require_tier("pro")
require_custom = require_tier("custom")


def require_feature(feature: str):
    """Create a dependency that requires a specific feature.

    This decorator checks if the user's tier has access to the specified feature.
    Features include: api_access, area_code_selection, isp_filtering, webhooks, etc.

    Args:
        feature: Feature name to check access for

    Returns:
        Dependency function that validates feature access

    Raises:
        HTTPException 403 if user doesn't have access to feature
    """

    def feature_dependency(
        request: Request,
        user_id: str = Depends(get_current_user_id),
        db: Session = Depends(get_db),
    ) -> str:
        """Validate user has access to feature and return user_id if authorized."""
        try:
            # Get tier_manager from request state (set by middleware)
            tier_manager = getattr(request.state, "tier_manager", None)
            if not tier_manager:
                tier_manager = TierManager(db)

            # Check feature access
            if not tier_manager.check_feature_access(user_id, feature):
                # Log unauthorized access attempt
                logger.warning(
                    f"TIER_ACCESS | status=DENIED | user={user_id} | feature={feature} | "
                    f"reason=insufficient_tier"
                )
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Feature '{feature}' requires higher tier",
                )

            # Log authorized access
            logger.debug(
                f"TIER_ACCESS | status=ALLOWED | user={user_id} | feature={feature}"
            )
            return user_id

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Feature access check failed: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to verify feature access",
            )

    return feature_dependency


# Common feature dependencies
require_api_access = require_feature("api_access")
require_area_codes = require_feature("area_code_selection")
require_isp_filtering = require_feature("isp_filtering")
require_webhooks = require_feature("webhooks")
require_priority_routing = require_feature("priority_routing")
require_custom_branding = require_feature("custom_branding")


def require_payment_method(
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
) -> str:
    """Block access if no card on file and balance is below $1."""
    from app.models.user import User as _User
    from app.models.user_preference import UserPreference

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
