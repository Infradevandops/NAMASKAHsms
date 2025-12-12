"""Tier configuration and feature definitions."""
from typing import Dict, Any


class TierConfig:
    """Configuration for all subscription tiers."""
    
    FREEMIUM = {
        "name": "Freemium",
        "tier": "freemium",
        "price_monthly": 0,  # cents
        "payment_required": False,
        "has_api_access": False,
        "has_area_code_selection": False,
        "has_isp_filtering": False,
        "api_key_limit": 0,  # No API keys
        "daily_verification_limit": 100,
        "monthly_verification_limit": 3000,
        "country_limit": 5,
        "sms_retention_days": 1,
        "support_level": "community",
        "rate_limit_per_minute": 10,
        "rate_limit_per_hour": 100,
        "features": {
            "webhooks": False,
            "priority_routing": False,
            "custom_branding": False,
        }
    }
    
    STARTER = {
        "name": "Starter",
        "tier": "starter",
        "price_monthly": 900,  # $9.00 in cents
        "payment_required": True,
        "has_api_access": True,
        "has_area_code_selection": True,  # Key feature
        "has_isp_filtering": False,
        "api_key_limit": 5,
        "daily_verification_limit": 1000,
        "monthly_verification_limit": 30000,
        "country_limit": 20,
        "sms_retention_days": 7,
        "support_level": "email",
        "rate_limit_per_minute": 50,
        "rate_limit_per_hour": 1000,
        "features": {
            "webhooks": True,
            "priority_routing": False,
            "custom_branding": False,
        }
    }
    
    TURBO = {
        "name": "Turbo",
        "tier": "turbo",
        "price_monthly": 1399,  # $13.99 in cents
        "payment_required": True,
        "has_api_access": True,
        "has_area_code_selection": True,
        "has_isp_filtering": True,  # Premium feature
        "api_key_limit": -1,  # Unlimited
        "daily_verification_limit": 10000,
        "monthly_verification_limit": 300000,
        "country_limit": -1,  # All countries
        "sms_retention_days": 30,
        "support_level": "priority",
        "rate_limit_per_minute": 200,
        "rate_limit_per_hour": 10000,
        "features": {
            "webhooks": True,
            "priority_routing": True,
            "custom_branding": True,
        }
    }
    
    @classmethod
    def get_tier_config(cls, tier: str) -> Dict[str, Any]:
        """Get configuration for a specific tier."""
        tier_map = {
            "freemium": cls.FREEMIUM,
            "starter": cls.STARTER,
            "turbo": cls.TURBO,
        }
        return tier_map.get(tier.lower(), cls.FREEMIUM)
    
    @classmethod
    def get_all_tiers(cls) -> list:
        """Get all available tiers."""
        return [cls.FREEMIUM, cls.STARTER, cls.TURBO]
    
    @classmethod
    def get_tier_price(cls, tier: str) -> int:
        """Get monthly price in cents for a tier."""
        config = cls.get_tier_config(tier)
        return config["price_monthly"]
