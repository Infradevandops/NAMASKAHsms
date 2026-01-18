"""Quota tracking and overage calculation service."""

from datetime import datetime, date
from sqlalchemy.orm import Session
from app.models.user import User
from app.core.tier_config_simple import TIER_CONFIG


class QuotaService:
    """Manage user quotas and overage charges."""

    @staticmethod
    def get_monthly_usage(db: Session, user_id: str, month: str = None) -> dict:
        """Get quota usage for a month.

        Args:
            db: Database session
            user_id: User ID
            month: Month in format "2025-01" (defaults to current month)

        Returns:
            dict with quota_used, overage_used, quota_limit
        """
        if not month:
            month = datetime.now().strftime("%Y-%m")

        from app.models.user_quota import MonthlyQuotaUsage

        usage = (
            db.query(MonthlyQuotaUsage)
            .filter(MonthlyQuotaUsage.user_id == user_id, MonthlyQuotaUsage.month == month)
            .first()
        )

        user = db.query(User).filter(User.id == user_id).first()
        tier = TIER_CONFIG.get(user.subscription_tier, {})
        quota_limit = tier.get("quota_usd", 0)

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
    def add_quota_usage(db: Session, user_id: str, amount: float, month: str = None) -> None:
        """Add to quota usage.

        Args:
            db: Database session
            user_id: User ID
            amount: Amount to add (in USD)
            month: Month in format "2025-01" (defaults to current month)
        """
        if not month:
            month = datetime.now().strftime("%Y-%m")

        from app.models.user_quota import MonthlyQuotaUsage
        import uuid

        usage = (
            db.query(MonthlyQuotaUsage)
            .filter(MonthlyQuotaUsage.user_id == user_id, MonthlyQuotaUsage.month == month)
            .first()
        )

        if not usage:
            usage = MonthlyQuotaUsage(
                id=str(uuid.uuid4()), user_id=user_id, month=month, quota_used=0.0, overage_used=0.0
            )
            db.add(usage)

        usage.quota_used += amount
        db.commit()

    @staticmethod
    def calculate_overage(db: Session, user_id: str, cost: float, month: str = None) -> float:
        """Calculate overage charge if quota exceeded.

        Args:
            db: Database session
            user_id: User ID
            cost: Cost of SMS in USD
            month: Month in format "2025-01"

        Returns:
            Overage charge (0 if within quota)
        """
        if not month:
            month = datetime.now().strftime("%Y-%m")

        usage = QuotaService.get_monthly_usage(db, user_id, month)
        quota_limit = usage["quota_limit"]
        quota_used = usage["quota_used"]

        if quota_used + cost > quota_limit:
            user = db.query(User).filter(User.id == user_id).first()
            tier = TIER_CONFIG.get(user.subscription_tier, {})
            overage_rate = tier.get("overage_rate", 0)

            overage_amount = (quota_used + cost) - quota_limit
            return overage_amount * overage_rate

        return 0.0

    @staticmethod
    def reset_monthly_quota(db: Session, user_id: str) -> None:
        """Reset monthly quota (called on month boundary).

        Args:
            db: Database session
            user_id: User ID
        """
        user = db.query(User).filter(User.id == user_id).first()
        if user:
            user.monthly_quota_used = 0.0
            user.monthly_quota_reset_date = date.today()
            db.commit()

    @staticmethod
    def get_overage_rate(db: Session, user_id: str) -> float:
        """Get overage rate for user's tier.

        Args:
            db: Database session
            user_id: User ID

        Returns:
            Overage rate (e.g., 0.30 for Pro tier)
        """
        user = db.query(User).filter(User.id == user_id).first()
        tier = TIER_CONFIG.get(user.subscription_tier, {})
        return tier.get("overage_rate", 0)
