"""Tier configuration and feature definitions - Updated for 4-tier system."""


from typing import Any, Dict
from sqlalchemy import text
from sqlalchemy.orm import Session

class TierConfig:

    """Configuration for all subscription tiers - Database-driven."""

    @classmethod
def get_tier_config(cls, tier: str, db: Session = None) -> Dict[str, Any]:

        """Get configuration for a specific tier from database."""
if not db:
            # Fallback to hardcoded config if no DB session
            return cls._get_fallback_config(tier)

        result = db.execute(
            text(
                """
            SELECT tier, name, price_monthly, quota_usd, overage_rate,
                   has_api_access, has_area_code_selection, has_isp_filtering,
                   api_key_limit, support_level, daily_verification_limit,
                   monthly_verification_limit, country_limit, sms_retention_days,
                   rate_limit_per_minute, rate_limit_per_hour
            FROM subscription_tiers
            WHERE tier = :tier
        """
            ),
            {"tier": tier},
        )

        row = result.fetchone()
if not row:
            return cls._get_fallback_config("freemium")

        return {
            "name": row[1],
            "tier": row[0],
            "price_monthly": row[2],  # Keep in cents for API consistency
            "quota_usd": row[3],
            "overage_rate": row[4],
            "payment_required": row[2] > 0,
            "has_api_access": bool(row[5]),
            "has_area_code_selection": bool(row[6]),
            "has_isp_filtering": bool(row[7]),
            "api_key_limit": row[8],
            "support_level": row[9],
            "daily_verification_limit": row[10],
            "monthly_verification_limit": row[11],
            "country_limit": row[12],
            "sms_retention_days": row[13],
            "rate_limit_per_minute": row[14],
            "rate_limit_per_hour": row[15],
            "features": {
                "webhooks": bool(row[5]),  # API access enables webhooks
                "priority_routing": tier in ["pro", "custom"],
                "custom_branding": tier == "custom",
            },
        }

    @classmethod
def get_all_tiers(cls, db: Session = None) -> list:

        """Get all available tiers from database."""
if not db:
            return cls._get_fallback_tiers()

        result = db.execute(
            text(
                """
            SELECT tier, name, price_monthly, quota_usd, overage_rate,
                   has_api_access, has_area_code_selection, has_isp_filtering,
                   api_key_limit, support_level, daily_verification_limit,
                   monthly_verification_limit, country_limit, sms_retention_days,
                   rate_limit_per_minute, rate_limit_per_hour
            FROM subscription_tiers
            ORDER BY price_monthly
        """
            )
        )

        tiers = []
for row in result.fetchall():
            tier_config = {
                "name": row[1],
                "tier": row[0],
                "price_monthly": row[2],
                "quota_usd": row[3],
                "overage_rate": row[4],
                "payment_required": row[2] > 0,
                "has_api_access": bool(row[5]),
                "has_area_code_selection": bool(row[6]),
                "has_isp_filtering": bool(row[7]),
                "api_key_limit": row[8],
                "support_level": row[9],
                "daily_verification_limit": row[10],
                "monthly_verification_limit": row[11],
                "country_limit": row[12],
                "sms_retention_days": row[13],
                "rate_limit_per_minute": row[14],
                "rate_limit_per_hour": row[15],
                "features": {
                    "webhooks": bool(row[5]),
                    "priority_routing": row[0] in ["pro", "custom"],
                    "custom_branding": row[0] == "custom",
                },
            }
            tiers.append(tier_config)

        return tiers

    @classmethod
def get_tier_price(cls, tier: str, db: Session = None) -> int:

        """Get monthly price in cents for a tier."""
        config = cls.get_tier_config(tier, db)
        return config["price_monthly"]

    @classmethod
def _get_fallback_config(cls, tier: str) -> Dict[str, Any]:

        """Fallback configuration when database is unavailable."""
        fallback_tiers = {
            "freemium": {
                "name": "Freemium",
                "tier": "freemium",
                "price_monthly": 0,
                "quota_usd": 0,
                "base_sms_cost": 2.50,
                "overage_rate": 2.22,
                "payment_required": False,
                "has_api_access": False,
                "has_area_code_selection": False,
                "has_isp_filtering": False,
                "api_key_limit": 0,
                "support_level": "community",
                "daily_verification_limit": 100,
                "monthly_verification_limit": 3000,
                "country_limit": 5,
                "sms_retention_days": 1,
                "rate_limit_per_minute": 10,
                "rate_limit_per_hour": 100,
                "features": {
                    "webhooks": False,
                    "priority_routing": False,
                    "custom_branding": False,
                },
            },
            "payg": {
                "name": "Pay-As-You-Go",
                "tier": "payg",
                "price_monthly": 0,
                "quota_usd": 0,
                "base_sms_cost": 2.50,
                "overage_rate": 2.50,
                "payment_required": False,
                "has_api_access": False,
                "has_area_code_selection": True,
                "has_isp_filtering": True,
                "api_key_limit": 0,
                "support_level": "community",
                "daily_verification_limit": 500,
                "monthly_verification_limit": 15000,
                "country_limit": -1,
                "sms_retention_days": 3,
                "rate_limit_per_minute": 30,
                "rate_limit_per_hour": 500,
                "features": {
                    "webhooks": False,
                    "priority_routing": False,
                    "custom_branding": False,
                },
            },
            "pro": {
                "name": "Pro",
                "tier": "pro",
                "price_monthly": 2500,
                "quota_usd": 15,
                "base_sms_cost": 2.50,
                "overage_rate": 0.30,
                "payment_required": True,
                "has_api_access": True,
                "has_area_code_selection": True,
                "has_isp_filtering": True,
                "api_key_limit": 10,
                "support_level": "priority",
                "daily_verification_limit": 2000,
                "monthly_verification_limit": 60000,
                "country_limit": -1,
                "sms_retention_days": 7,
                "rate_limit_per_minute": 100,
                "rate_limit_per_hour": 2000,
                "features": {
                    "webhooks": True,
                    "priority_routing": True,
                    "custom_branding": False,
                },
            },
            "custom": {
                "name": "Custom",
                "tier": "custom",
                "price_monthly": 3500,
                "quota_usd": 25,
                "base_sms_cost": 2.50,
                "overage_rate": 0.20,
                "payment_required": True,
                "has_api_access": True,
                "has_area_code_selection": True,
                "has_isp_filtering": True,
                "api_key_limit": -1,
                "support_level": "dedicated",
                "daily_verification_limit": 10000,
                "monthly_verification_limit": 300000,
                "country_limit": -1,
                "sms_retention_days": 30,
                "rate_limit_per_minute": 500,
                "rate_limit_per_hour": 10000,
                "features": {
                    "webhooks": True,
                    "priority_routing": True,
                    "custom_branding": True,
                },
            },
        }
        return fallback_tiers.get(tier.lower(), fallback_tiers["freemium"])

    @classmethod
def _get_fallback_tiers(cls) -> list:

        """Fallback tier list when database is unavailable."""
        return [cls._get_fallback_config(tier) for tier in ["freemium", "payg", "pro", "custom"]]