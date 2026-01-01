"""Tier management service for subscription-based feature access."""
from typing import Optional
from sqlalchemy.orm import Session
from datetime import datetime, timezone

from app.models.user import User
from app.core.tier_config import TierConfig
from app.core.logging import get_logger

logger = get_logger(__name__)


class TierManager:
    """Manages user tier validation and feature access."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_user_tier(self, user_id: str) -> str:
        """Get user's current subscription tier."""
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            return "freemium"  # Default to freemium for non-existent users
        
        # Check if paid tier has expired
        if user.subscription_tier in ["pro", "custom"]:
            if user.tier_expires_at and user.tier_expires_at < datetime.now(timezone.utc):
                logger.warning(f"User {user_id} tier expired, downgrading to freemium")
                user.subscription_tier = "freemium"
                self.db.commit()
                return "freemium"
        
        return user.subscription_tier or "freemium"
    
    def check_feature_access(self, user_id: str, feature: str) -> bool:
        """Check if user has access to a specific feature."""
        tier = self.get_user_tier(user_id)
        config = TierConfig.get_tier_config(tier)
        
        feature_map = {
            "api_access": config["has_api_access"],
            "area_code_selection": config["has_area_code_selection"],
            "isp_filtering": config["has_isp_filtering"],
            "webhooks": config["features"].get("webhooks", False),
            "priority_routing": config["features"].get("priority_routing", False),
            "custom_branding": config["features"].get("custom_branding", False),
        }
        
        return feature_map.get(feature, False)
    
    def get_tier_limits(self, user_id: str) -> dict:
        """Get all limits for user's current tier."""
        tier = self.get_user_tier(user_id)
        config = TierConfig.get_tier_config(tier)
        
        return {
            "tier": tier,
            "api_key_limit": config["api_key_limit"],
            "daily_verification_limit": config["daily_verification_limit"],
            "monthly_verification_limit": config["monthly_verification_limit"],
            "country_limit": config["country_limit"],
            "sms_retention_days": config["sms_retention_days"],
            "rate_limit_per_minute": config["rate_limit_per_minute"],
            "rate_limit_per_hour": config["rate_limit_per_hour"],
        }
    
    def can_create_api_key(self, user_id: str) -> tuple[bool, Optional[str]]:
        """Check if user can create another API key."""
        from app.models.api_key import APIKey
        
        tier = self.get_user_tier(user_id)
        config = TierConfig.get_tier_config(tier)
        
        if not config["has_api_access"]:
            return False, "API access not available on Freemium tier. Upgrade to Starter or Turbo."
        
        # Count existing API keys
        existing_keys = self.db.query(APIKey).filter(
            APIKey.user_id == user_id,
            APIKey.is_active == True
        ).count()
        
        api_key_limit = config["api_key_limit"]
        
        # -1 means unlimited
        if api_key_limit == -1:
            return True, None
        
        if existing_keys >= api_key_limit:
            return False, f"API key limit reached ({api_key_limit} keys for {tier.title()} tier)"
        
        return True, None
    
    def upgrade_tier(self, user_id: str, new_tier: str) -> bool:
        """Upgrade user to a new tier."""
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            return False
        
        if new_tier not in ["freemium", "payg", "pro", "custom"]:
            logger.error(f"Invalid tier: {new_tier}")
            return False
        
        old_tier = user.subscription_tier
        user.subscription_tier = new_tier
        user.tier_upgraded_at = datetime.now(timezone.utc)
        
        # Set expiration for paid tiers (monthly)
        if new_tier in ["pro", "custom"]:
            from datetime import timedelta
            user.tier_expires_at = datetime.now(timezone.utc) + timedelta(days=30)
        else:
            user.tier_expires_at = None
        
        self.db.commit()
        logger.info(f"User {user_id} upgraded from {old_tier} to {new_tier}")
        return True
    
    def downgrade_tier(self, user_id: str, new_tier: str = "freemium") -> bool:
        """Downgrade user tier."""
        return self.upgrade_tier(user_id, new_tier)


def get_tier_manager(db: Session) -> TierManager:
    """Dependency injection for TierManager."""
    return TierManager(db)
