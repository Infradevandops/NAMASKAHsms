"""Tier helper functions for subscription tier management.

This module provides utility functions for working with user subscription tiers,
including tier hierarchy checks, access validation, and display name mapping.
"""

import logging
from datetime import datetime
from fastapi import HTTPException
from sqlalchemy.orm import Session
from app.models.user import User
from app.schemas.tier_response import TierAccessDenied


logger = logging.getLogger(__name__)


# Tier hierarchy - higher number = more access
TIER_HIERARCHY: dict[str, int] = {"freemium": 0, "payg": 1, "pro": 2, "custom": 3}

# Human-readable tier display names
TIER_DISPLAY_NAMES: dict[str, str] = {
    "freemium": "Freemium",
    "payg": "Pay-As-You-Go",
    "pro": "Pro",
    "custom": "Custom",
}


def get_user_tier(user_id: str, db: Session) -> str:

    """Get user's current subscription tier.

    Args:
        user_id: The unique identifier of the user
        db: Database session

    Returns:
        The user's subscription tier, or 'freemium' if user not found or tier is null
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        return "freemium"
    return user.subscription_tier or "freemium"


def has_tier_access(user_tier: str, required_tier: str) -> bool:
    """Check if user tier meets or exceeds required tier.

    Args:
        user_tier: The user's current tier
        required_tier: The minimum tier required for access

    Returns:
        True if user tier level >= required tier level, False otherwise
    """
    user_level = TIER_HIERARCHY.get(user_tier, 0)
    required_level = TIER_HIERARCHY.get(required_tier, 0)
    return user_level >= required_level


def is_subscribed(user_tier: str) -> bool:
    """Check if user has a paid subscription (payg or higher).

    Args:
        user_tier: The user's current tier

    Returns:
        True if user has a paid tier (payg, pro, or custom), False otherwise
    """
    return user_tier in ["payg", "pro", "custom"]


def get_tier_display_name(tier: str) -> str:
    """Get human-readable tier name.

    Args:
        tier: The tier code (freemium, payg, pro, custom)

    Returns:
        Human-readable tier name, or 'Unknown' if tier code not recognized
    """
    return TIER_DISPLAY_NAMES.get(tier, "Unknown")


def raise_tier_error(current_tier: str, required_tier: str, user_id: str = None):
    logger.warning(f"Tier access denied: user={user_id}, current={current_tier}, required={required_tier}")

    raise HTTPException(
        status_code=402,
        detail=TierAccessDenied(
            message=f"This feature requires {required_tier} tier or higher",
            current_tier=current_tier,
            required_tier=required_tier,
            timestamp=datetime.utcnow(),
        ).model_dump(mode="json"),
    )


def log_tier_check(user_id: str, endpoint: str, tier: str, allowed: bool):
    logger.info(
        "tier_check",
        extra={
            "user_id": user_id,
            "endpoint": endpoint,
            "tier": tier,
            "allowed": allowed,
            "timestamp": datetime.utcnow().isoformat(),
        },
    )
