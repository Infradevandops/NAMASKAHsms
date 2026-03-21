"""Quota tracking and overage calculation service."""

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
        """Get quota usage for a month.

        `tier` should be the value resolved by TierManager.get_user_tier() so that
        expired subscriptions use the correct (downgraded) limits.
        """
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
        """Calculate overage charge if quota exceeded."""
        if not month:
            month = datetime.now().strftime("%Y-%m")

        usage = QuotaService.get_monthly_usage(db, user_id, month, tier=tier)
        quota_limit = usage["quota_limit"]
        quota_used = usage["quota_used"]

        if quota_used + cost > quota_limit:
            if tier is None:
                user = db.query(User).filter(User.id == user_id).first()
                tier = user.subscription_tier if user else "freemium"
            tier_config = TierConfig.get_tier_config(tier, db)
            overage_rate = tier_config.get("overage_rate", 0)
            overage_amount = (quota_used + cost) - quota_limit
            return overage_amount * overage_rate

        return 0.0

    @staticmethod
    def reset_monthly_quota(db: Session, user_id: str) -> None:
        """Reset monthly quota (called on month boundary)."""
        user = db.query(User).filter(User.id == user_id).first()
        if user:
            user.monthly_quota_used = 0.0
            user.monthly_quota_reset_date = date.today()
            db.commit()

    @staticmethod
    def get_overage_rate(db: Session, user_id: str) -> float:
        """Get overage rate for user's tier."""
        user = db.query(User).filter(User.id == user_id).first()
        tier = TierConfig.get_tier_config(user.subscription_tier, db)
        return tier.get("overage_rate", 0)
