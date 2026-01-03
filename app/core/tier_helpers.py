"""Tier helper functions for subscription tier management.

This module provides utility functions for working with user subscription tiers,
including tier hierarchy checks, access validation, and display name mapping.
"""
from typing import Optional
from sqlalchemy.orm import Session

from app.models.user import User


# Tier hierarchy - higher number = more access
TIER_HIERARCHY: dict[str, int] = {
    "freemium": 0,
    "payg": 1,
    "pro": 2,
    "custom": 3
}

# Human-readable tier display names
TIER_DISPLAY_NAMES: dict[str, str] = {
    "freemium": "Freemium",
    "payg": "Pay-As-You-Go",
    "pro": "Pro",
    "custom": "Custom"
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
