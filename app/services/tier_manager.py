"""Tier management service for subscription tiers and feature access."""

from datetime import datetime, timezone
from typing import Dict, List, Optional

from sqlalchemy.orm import Session

from app.core.logging import get_logger
from app.core.tier_config import TierConfig
from app.models.user import User

logger = get_logger(__name__)


class TierManager:
    """Manages user subscription tiers and feature access."""

    def __init__(self, db: Session):
        self.db = db

    def get_user_tier(self, user_id: str) -> str:
        """Get user's current subscription tier.

        Forces a fresh DB read to prevent stale SQLAlchemy identity-map data
        from returning a default/outdated tier value.
        """
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            return "freemium"

        # Force reload from DB to avoid stale session cache
        try:
            self.db.refresh(user)
        except Exception:
            # Detached or transient instance — re-query
            self.db.expire_all()
            user = self.db.query(User).filter(User.id == user_id).first()
            if not user:
                return "freemium"

        # Admins always keep their assigned tier — never subject to expiry
        if getattr(user, "is_admin", False):
            tier = user.subscription_tier
            return tier if tier in {"freemium", "payg", "pro", "custom"} else "custom"

        tier = user.subscription_tier or "freemium"

        # Validate tier is a known value — unknown tiers fall back to freemium
        valid_tiers = {"freemium", "payg", "pro", "custom"}
        if tier not in valid_tiers:
            logger.warning(
                f"User {user_id} has unknown tier '{tier}', defaulting to freemium"
            )
            tier = "freemium"

        # Only auto-downgrade if tier_expires_at is explicitly set (not None)
        expires = getattr(user, "tier_expires_at", None)
        if expires is not None and tier in ("pro", "custom"):
            if expires.tzinfo is None:
                expires = expires.replace(tzinfo=timezone.utc)

            if expires < datetime.now(timezone.utc):
                logger.warning(
                    f"User {user_id} tier '{tier}' expired at {expires.isoformat()}, "
                    "downgrading to freemium"
                )
                user.subscription_tier = "freemium"
                user.tier_expires_at = None
                self.db.commit()
                tier = "freemium"

        return tier

    def check_feature_access(self, user_id: str, feature: str) -> bool:
        """Check if user has access to a specific feature."""
        tier = self.get_user_tier(user_id)
        config = TierConfig.get_tier_config(tier, self.db)

        # Check specific features
        feature_map = {
            "api_access": config.get("has_api_access", False),
            "area_code_selection": config.get("has_area_code_selection", False),
            "isp_filtering": config.get("has_isp_filtering", False),
            "webhooks": config.get("features", {}).get("webhooks", False),
            "priority_routing": config.get("features", {}).get(
                "priority_routing", False
            ),
            "custom_branding": config.get("features", {}).get("custom_branding", False),
        }

        return feature_map.get(feature, False)

    def get_tier_limits(self, user_id: str) -> Dict:
        """Get tier limits for user."""
        tier = self.get_user_tier(user_id)
        config = TierConfig.get_tier_config(tier, self.db)

        return {
            "daily_verification_limit": config.get("daily_verification_limit", 100),
            "monthly_verification_limit": config.get(
                "monthly_verification_limit", 3000
            ),
            "api_key_limit": config.get("api_key_limit", 0),
            "rate_limit_per_minute": config.get("rate_limit_per_minute", 10),
            "rate_limit_per_hour": config.get("rate_limit_per_hour", 100),
        }

    def upgrade_user_tier(
        self, user_id: str, new_tier: str, expires_at: Optional[datetime] = None
    ) -> bool:
        """Upgrade user to a new tier."""
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            return False

        # Validate tier
        valid_tiers = ["freemium", "payg", "pro", "custom"]
        if new_tier not in valid_tiers:
            return False

        user.subscription_tier = new_tier
        if expires_at:
            user.tier_expires_at = expires_at

        self.db.commit()
        logger.info(f"User {user_id} upgraded to {new_tier} tier")
        return True

    def downgrade_user_tier(self, user_id: str, reason: str = "manual") -> bool:
        """Downgrade user to freemium tier."""
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            return False

        user.subscription_tier = "freemium"
        user.tier_expires_at = None

        self.db.commit()
        logger.info(f"User {user_id} downgraded to freemium tier - reason: {reason}")
        return True

    def get_all_tiers(self) -> List[Dict]:
        """Get all available tiers with their configurations."""
        return TierConfig.get_all_tiers(self.db)

    def can_create_api_key(self, user_id: str) -> tuple[bool, str]:
        """Check if user can create another API key based on their tier limit."""
        from app.models.api_key import APIKey

        tier = self.get_user_tier(user_id)
        config = TierConfig.get_tier_config(tier, self.db)
        limit = config.get("api_key_limit", 0)

        if limit == 0:
            return (
                False,
                f"API key access requires Pro tier or higher. Current tier: {tier}",
            )

        if limit == -1:  # unlimited
            return True, ""

        active_count = (
            self.db.query(APIKey)
            .filter(APIKey.user_id == user_id, APIKey.is_active.is_(True))
            .count()
        )

        if active_count >= limit:
            return (
                False,
                f"API key limit reached ({limit}/{limit}). Revoke an existing key to create a new one.",
            )

        return True, ""

    def check_tier_hierarchy(self, current_tier: str, required_tier: str) -> bool:
        """Check if current tier meets or exceeds required tier."""
        tier_hierarchy = {"freemium": 0, "payg": 1, "pro": 2, "custom": 3}

        current_level = tier_hierarchy.get(current_tier, 0)
        required_level = tier_hierarchy.get(required_tier, 0)

        return current_level >= required_level
