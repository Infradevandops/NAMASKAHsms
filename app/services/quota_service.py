"""Quota tracking service.

v5.1: Overage now uses tier-specific overage_rate.
  - Freemium/PAYG: No quota. Overage is always 0. They pay base_cost directly.
  - Pro/Custom: Have a monthly USD quota from their subscription.
    Within quota → cost is covered (overage = 0).
    Over quota → they pay overage_rate per SMS (Pro: $1.80, Custom: $1.50).
    Both rates are profitable vs $1.46 provider cost.
"""

import uuid
from datetime import date, datetime

from sqlalchemy.orm import Session

from app.core.tier_config import TierConfig
from app.models.user import User
from app.models.user_quota import MonthlyQuotaUsage


class QuotaService:
    """Manage user quotas and overage charges."""

    @staticmethod
    def get_monthly_usage(
        db: Session, user_id: str, month: str = None, tier: str = None
    ) -> dict:
        """Get quota usage for a month."""
        if not month:
            month = datetime.now().strftime("%Y-%m")

        usage = (
            db.query(MonthlyQuotaUsage)
            .filter(
                MonthlyQuotaUsage.user_id == user_id, MonthlyQuotaUsage.month == month
            )
            .first()
        )

        if tier is None:
            user = db.query(User).filter(User.id == user_id).first()
            tier = user.subscription_tier if user else "freemium"

        tier_config = TierConfig.get_tier_config(tier, db)
        quota_limit = tier_config.get("quota_usd", 0)

        if not usage:
            return {
                "quota_used": 0.0,
                "overage_used": 0.0,
                "quota_limit": quota_limit,
                "remaining": quota_limit,
            }

        return {
            "quota_used": usage.quota_used,
            "overage_used": usage.overage_used,
            "quota_limit": quota_limit,
            "remaining": max(0, quota_limit - usage.quota_used),
        }

    @staticmethod
    def add_quota_usage(
        db: Session, user_id: str, amount: float, month: str = None
    ) -> None:
        """Add to quota usage."""
        if not month:
            month = datetime.now().strftime("%Y-%m")

        usage = (
            db.query(MonthlyQuotaUsage)
            .filter(
                MonthlyQuotaUsage.user_id == user_id, MonthlyQuotaUsage.month == month
            )
            .first()
        )

        if not usage:
            usage = MonthlyQuotaUsage(
                id=str(uuid.uuid4()),
                user_id=user_id,
                month=month,
                quota_used=0.0,
                overage_used=0.0,
            )
            db.add(usage)

        usage.quota_used += amount
        db.commit()

    @staticmethod
    def calculate_overage(
        db: Session, user_id: str, cost: float, month: str = None, tier: str = None
    ) -> float:
        """Calculate overage charge.

        - Freemium/PAYG (quota_limit=0): Always returns 0.
          These tiers pay the base cost directly.
        - Pro/Custom (quota_limit>0): If within quota, returns 0 (subscription
          covers it). If over quota, charges overage_rate per SMS:
          Pro: $1.80/SMS (23% margin over $1.46 provider cost)
          Custom: $1.50/SMS (2.7% margin over $1.46 provider cost)
        """
        if not month:
            month = datetime.now().strftime("%Y-%m")

        usage = QuotaService.get_monthly_usage(db, user_id, month, tier=tier)
        quota_limit = usage["quota_limit"]

        # No quota means no overage system — user pays base cost directly
        if quota_limit <= 0:
            return 0.0

        quota_used = usage["quota_used"]

        # Within quota — subscription covers it
        if quota_used + cost <= quota_limit:
            return 0.0

        # Get tier overage_rate
        if tier is None:
            user = db.query(User).filter(User.id == user_id).first()
            tier = user.subscription_tier if user else "freemium"
        tier_config = TierConfig.get_tier_config(tier, db)
        overage_rate = tier_config.get("overage_rate", cost)

        # Over quota — charge overage_rate for the excess portion
        if quota_used >= quota_limit:
            # Fully exhausted — entire SMS charged at overage_rate
            return round(overage_rate, 2)
        else:
            # Partially covered — only the excess portion charged at overage_rate
            # Fraction of SMS that exceeds quota
            excess_fraction = ((quota_used + cost) - quota_limit) / cost
            return round(overage_rate * excess_fraction, 2)

    @staticmethod
    def reset_monthly_quota(db: Session, user_id: str) -> None:
        """Reset monthly quota (called on month boundary)."""
        user = db.query(User).filter(User.id == user_id).first()
        if user:
            user.monthly_quota_used = 0.0
            user.monthly_quota_reset_date = date.today()
            db.commit()
