"""Pricing calculation service."""

from sqlalchemy.orm import Session

from app.core.tier_config_simple import TIER_CONFIG
from app.models.user import User
from app.services.quota_service import QuotaService


class PricingCalculator:
    """Calculate SMS verification costs."""

    @staticmethod
    def calculate_sms_cost(db: Session, user_id: str, filters: dict = None) -> dict:
        """Calculate total cost for SMS verification."""
        if not filters:
            filters = {}

        user = db.query(User).filter(User.id == user_id).first()
        tier = TIER_CONFIG.get(user.subscription_tier, {})

        base_cost = tier.get("base_sms_cost", 2.50)

        filter_charges = 0.0
        if user.subscription_tier == "payg":
            if filters.get("state") or filters.get("city"):
                filter_charges += 0.25
            if filters.get("isp"):
                filter_charges += 0.50

        if user.subscription_tier == "freemium" and any(filters.values()):
            raise ValueError("Filters not available for Freemium tier")

        overage_charge = QuotaService.calculate_overage(
            db, user_id, base_cost + filter_charges
        )
        total_cost = base_cost + filter_charges + overage_charge

        return {
            "base_cost": base_cost,
            "filter_charges": filter_charges,
            "overage_charge": overage_charge,
            "total_cost": total_cost,
            "tier": user.subscription_tier,
        }

    @staticmethod
    def get_filter_charges(db: Session, user_id: str, filters: dict) -> float:
        """Get filter charges for user's tier."""
        user = db.query(User).filter(User.id == user_id).first()

        if user.subscription_tier == "freemium":
            if any(filters.values()):
                raise ValueError("Filters not available for Freemium tier")
            return 0.0

        if user.subscription_tier == "payg":
            charges = 0.0
            if filters.get("state") or filters.get("city"):
                charges += 0.25
            if filters.get("isp"):
                charges += 0.50
            return charges

        return 0.0

    @staticmethod
    def validate_balance(db: Session, user_id: str, cost: float) -> bool:
        """Check if user has sufficient balance."""
        user = db.query(User).filter(User.id == user_id).first()

        if user.subscription_tier == "freemium":
            return user.bonus_sms_balance >= 1

        return user.credits >= cost

    @staticmethod
    def get_pricing_breakdown(db: Session, user_id: str, filters: dict = None) -> dict:
        """Get detailed pricing breakdown."""
        if not filters:
            filters = {}

        user = db.query(User).filter(User.id == user_id).first()
        tier = TIER_CONFIG.get(user.subscription_tier, {})

        cost_info = PricingCalculator.calculate_sms_cost(db, user_id, filters)
        quota_info = QuotaService.get_monthly_usage(db, user_id)

        return {
            "tier": user.subscription_tier,
            "tier_name": tier.get("name", "Unknown"),
            "base_cost": cost_info["base_cost"],
            "filter_charges": cost_info["filter_charges"],
            "overage_charge": cost_info["overage_charge"],
            "total_cost": cost_info["total_cost"],
            "quota_limit": quota_info["quota_limit"],
            "quota_used": quota_info["quota_used"],
            "quota_remaining": quota_info["remaining"],
            "user_balance": user.credits,
            "bonus_sms": (
                user.bonus_sms_balance if user.subscription_tier == "freemium" else 0
            ),
            "sufficient_balance": PricingCalculator.validate_balance(
                db, user_id, cost_info["total_cost"]
            ),
        }
