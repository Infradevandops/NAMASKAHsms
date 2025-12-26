"""
Pricing Calculator Service
Handles quota/overage logic for the 4-tier pricing system
"""

from typing import Dict, Any
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import text


class PricingCalculator:
    """Calculate SMS costs based on user tier and monthly usage."""

    BASE_SMS_COST = 2.50  # TextVerified base cost per SMS

    def __init__(self, db: Session):
        self.db = db

    def get_tier_config(self, tier: str) -> Dict[str, Any]:
        """Get tier configuration from database."""
        result = self.db.execute(text("""
            SELECT tier, name, price_monthly, quota_usd, overage_rate,
                   has_api_access, has_area_code_selection, has_isp_filtering,
                   api_key_limit, support_level
            FROM subscription_tiers
            WHERE tier = :tier
        """), {"tier": tier})

        row = result.fetchone()
        if not row:
            # Default to Pay-As-You-Go if tier not found
            return self.get_tier_config("payg")

        return {
            "tier": row[0],
            "name": row[1],
            "price_monthly": row[2] / 100,  # Convert cents to dollars
            "quota_usd": row[3],
            "overage_rate": row[4],
            "has_api_access": bool(row[5]),
            "has_area_code_selection": bool(row[6]),
            "has_isp_filtering": bool(row[7]),
            "api_key_limit": row[8],
            "support_level": row[9]
        }

    def get_monthly_usage(self, user_id: str) -> Dict[str, Any]:
        """Get user's current month usage."""
        current_month = datetime.now().strftime("%Y-%m")

        result = self.db.execute(text("""
            SELECT quota_used_usd, sms_count
            FROM user_quotas
            WHERE user_id = :user_id AND month_year = :month_year
        """), {"user_id": user_id, "month_year": current_month})

        row = result.fetchone()
        if row:
            return {
                "quota_used_usd": float(row[0]),
                "sms_count": int(row[1]),
                "month_year": current_month
            }
        else:
            return {
                "quota_used_usd": 0.0,
                "sms_count": 0,
                "month_year": current_month
            }

    def calculate_sms_cost(self, user_id: str, user_tier: str) -> Dict[str, Any]:
        """Calculate the cost for one SMS based on user tier and current usage."""
        tier_config = self.get_tier_config(user_tier)
        monthly_usage = self.get_monthly_usage(user_id)

        if user_tier == "payg":
            # Pay-As-You-Go: Always $2.50/SMS
            return {
                "cost_per_sms": self.BASE_SMS_COST,
                "within_quota": False,
                "quota_remaining_usd": 0,
                "quota_remaining_sms": 0,
                "tier_name": tier_config["name"],
                "pricing_type": "pay_as_you_go"
            }

        # Subscription tiers: Check quota
        quota_usd = tier_config["quota_usd"]
        quota_used_usd = monthly_usage["quota_used_usd"]
        quota_remaining_usd = max(0, quota_usd - quota_used_usd)

        # Calculate remaining SMS in quota (assuming $2.50 per SMS)
        quota_remaining_sms = int(quota_remaining_usd / self.BASE_SMS_COST)

        if quota_remaining_usd >= self.BASE_SMS_COST:
            # Within quota - SMS is "free" (covered by subscription)
            cost_per_sms = 0.0
            within_quota = True
        else:
            # Over quota - pay base cost + overage
            cost_per_sms = self.BASE_SMS_COST + tier_config["overage_rate"]
            within_quota = False

        return {
            "cost_per_sms": cost_per_sms,
            "within_quota": within_quota,
            "quota_remaining_usd": quota_remaining_usd,
            "quota_remaining_sms": quota_remaining_sms,
            "tier_name": tier_config["name"],
            "pricing_type": "subscription",
            "overage_rate": tier_config["overage_rate"] if not within_quota else 0
        }

    def record_sms_usage(self, user_id: str, cost_charged: float) -> None:
        """Record SMS usage for quota tracking."""
        current_month = datetime.now().strftime("%Y-%m")

        # Insert or update usage record
        self.db.execute(text("""
            INSERT INTO user_quotas (id, user_id, month_year, quota_used_usd, sms_count)
            VALUES (:id, :user_id, :month_year, :quota_used_usd, 1)
            ON CONFLICT(user_id, month_year) DO UPDATE SET
                quota_used_usd = quota_used_usd + :quota_used_usd,
                sms_count = sms_count + 1,
                updated_at = CURRENT_TIMESTAMP
        """), {
            "id": f"{user_id}_{current_month}",
            "user_id": user_id,
            "month_year": current_month,
            "quota_used_usd": self.BASE_SMS_COST  # Always count $2.50 against quota
        })

        self.db.commit()

    def get_pricing_summary(self, user_id: str, user_tier: str) -> Dict[str, Any]:
        """Get complete pricing summary for user dashboard."""
        tier_config = self.get_tier_config(user_tier)
        monthly_usage = self.get_monthly_usage(user_id)
        sms_cost = self.calculate_sms_cost(user_id, user_tier)

        return {
            "tier": tier_config,
            "monthly_usage": monthly_usage,
            "next_sms_cost": sms_cost,
            "features": {
                "api_access": tier_config["has_api_access"],
                "area_code_selection": tier_config["has_area_code_selection"],
                "isp_filtering": tier_config["has_isp_filtering"],
                "api_key_limit": tier_config["api_key_limit"],
                "support_level": tier_config["support_level"]
            }
        }

    def get_all_tiers(self) -> list:
        """Get all available tiers for pricing display."""
        result = self.db.execute(text("""
            SELECT tier, name, price_monthly, quota_usd, overage_rate,
                   has_api_access, has_area_code_selection, has_isp_filtering,
                   api_key_limit, support_level
            FROM subscription_tiers
            ORDER BY price_monthly
        """))

        tiers = []
        for row in result.fetchall():
            tier = {
                "tier": row[0],
                "name": row[1],
                "price_monthly": row[2] / 100,  # Convert cents to dollars
                "quota_usd": row[3],
                "overage_rate": row[4],
                "has_api_access": bool(row[5]),
                "has_area_code_selection": bool(row[6]),
                "has_isp_filtering": bool(row[7]),
                "api_key_limit": row[8],
                "support_level": row[9]
            }

            # Add calculated fields
            if tier["tier"] == "payg":
                tier["cost_per_sms"] = self.BASE_SMS_COST
                tier["quota_sms"] = 0
            else:
                tier["quota_sms"] = int(tier["quota_usd"] / self.BASE_SMS_COST)
                tier["overage_cost"] = self.BASE_SMS_COST + tier["overage_rate"]

            tiers.append(tier)

        return tiers
