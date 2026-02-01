"""Tier Validation Middleware for Feature Access Control."""


from fastapi import HTTPException, status
from app.models.user import User

TIER_HIERARCHY = {
    "freemium": ["freemium"],
    "payg": ["payg", "pro", "custom"],
    "pro": ["pro", "custom"],
    "custom": ["custom"],
}

TIER_FEATURES = {
    "area_code_selection": ["payg", "pro", "custom"],
    "carrier_selection": ["pro", "custom"],
    "api_access": ["pro", "custom"],
    "location_filters": ["payg", "pro", "custom"],
    "isp_filters": ["payg", "pro", "custom"],
}


def require_tier(user: User, feature: str):

    """Validate user has required tier for feature.

    Args:
        user: User object
        feature: Feature name to check

    Raises:
        HTTPException: If user doesn't have required tier

    Returns:
        True if user has access
    """
    required_tiers = TIER_FEATURES.get(feature, [])

if user.tier not in required_tiers:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "error": "upgrade_required",
                "message": f"This feature requires {required_tiers[0].upper()} tier or higher",
                "feature": feature,
                "current_tier": user.tier,
                "required_tiers": required_tiers,
            },
        )
    return True


def validate_tier_access(user: User, carrier: str = None, area_code: str = None):

    """Validate tier access for verification parameters.

    Args:
        user: User object
        carrier: Optional carrier selection
        area_code: Optional area code selection

    Raises:
        HTTPException: If user doesn't have required tier

    Returns:
        True if user has access
    """
if carrier and carrier.lower() not in ["any", "", "none"]:
        require_tier(user, "carrier_selection")

if area_code and area_code not in ["any", "", "none"]:
        require_tier(user, "area_code_selection")

    return True