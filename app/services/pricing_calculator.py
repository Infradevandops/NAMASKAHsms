"""Pricing calculation service."""

from sqlalchemy.orm import Session

from app.core.tier_config import TierConfig
from app.models.user import User
from app.services.quota_service import QuotaService


class PricingCalculator:
    """Calculate SMS verification costs."""

    # Carrier filter pricing (PAYG tier only)
    CARRIER_PREMIUMS = {
        "verizon": 0.30,
        "tmobile": 0.25,
        "t-mobile": 0.25,
        "att": 0.20,
        "at&t": 0.20,
        # Sprint merged with T-Mobile in 2020 - removed in v4.4.1
    }

    # Area code premiums (PAYG tier only)
    AREA_CODE_PREMIUMS = {
        "212": 0.50,
        "917": 0.50,
        "310": 0.50,
        "415": 0.50,
        "312": 0.40,
        "404": 0.40,
        "617": 0.40,
        "702": 0.30,
    }

    @staticmethod
    def calculate_sms_cost(db: Session, user_id: str, filters: dict = None) -> dict:
        """Calculate total cost for SMS verification.

        Raises ValueError if price is None (validation for Task 4.2).
        """
        if not filters:
            filters = {}

        user = db.query(User).filter(User.id == user_id).first()
        tier_name = user.subscription_tier
        tier = TierConfig.get_tier_config(tier_name, db)

        base_cost = tier.get("base_sms_cost", 2.50)

        # VALIDATION: Block purchase without price (Task 4.2)
        if base_cost is None:
            raise ValueError(
                f"Cannot purchase SMS: base cost is not configured for tier '{tier_name}'. "
                "Please contact support."
            )

        # Track individual surcharges (v4.4.1)
        carrier_premium = 0.0
        area_code_premium = 0.0

        if tier_name == "payg":
            # Area code premiums
            ac = filters.get("area_code")
            if ac:
                area_code_premium = PricingCalculator.AREA_CODE_PREMIUMS.get(
                    str(ac), 0.25
                )

            # Carrier premiums
            carrier = filters.get("carrier")
            if carrier:
                carrier_premium = PricingCalculator.CARRIER_PREMIUMS.get(
                    str(carrier).lower(), 0.50
                )

        filter_charges = carrier_premium + area_code_premium

        if tier_name == "freemium" and any(filters.values()):
            raise ValueError("Filters not available for Freemium tier")

        overage_charge = QuotaService.calculate_overage(
            db, user_id, base_cost + filter_charges, tier=tier_name
        )
        total_cost = base_cost + filter_charges + overage_charge

        # VALIDATION: Block purchase without total price (Task 4.2)
        if total_cost is None or total_cost <= 0:
            raise ValueError(
                f"Invalid pricing calculation: total_cost={total_cost}. "
                "Please contact support."
            )

        return {
            "base_cost": base_cost,
            "filter_charges": filter_charges,
            "overage_charge": overage_charge,
            "total_cost": total_cost,
            "tier": user.subscription_tier,
            "carrier_surcharge": carrier_premium,  # NEW (v4.4.1)
            "area_code_surcharge": area_code_premium,  # NEW (v4.4.1)
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
            ac = filters.get("area_code")
            if ac:
                charges += PricingCalculator.AREA_CODE_PREMIUMS.get(str(ac), 0.25)

            carrier = filters.get("carrier")
            if carrier:
                charges += PricingCalculator.CARRIER_PREMIUMS.get(
                    str(carrier).lower(), 0.50
                )
            return charges

        return 0.0

    @staticmethod
    def validate_balance(
        db: Session, user_id: str, cost: float, tier: str = None
    ) -> bool:
        """Check if user has sufficient balance.

        For pro/custom: passes if remaining quota covers the base cost.
        Credits are only required for the overage portion.
        `tier` should be the value from TierManager.get_user_tier() when available.
        """
        user = db.query(User).filter(User.id == user_id).first()
        resolved_tier = tier or user.subscription_tier

        if resolved_tier == "freemium":
            return user.bonus_sms_balance >= 1

        if resolved_tier in ("pro", "custom"):
            usage = QuotaService.get_monthly_usage(db, user_id, tier=resolved_tier)
            quota_remaining = usage["remaining"]
            tier_config = TierConfig.get_tier_config(resolved_tier, db)
            base_cost = tier_config.get("base_sms_cost", 0.30)
            if quota_remaining >= base_cost:
                return True  # within quota — subscription covers it
            # In overage: check credits cover the overage amount
            overage = QuotaService.calculate_overage(
                db, user_id, cost, tier=resolved_tier
            )
            return user.credits >= overage

        return user.credits >= cost

    @staticmethod
    def get_pricing_breakdown(db: Session, user_id: str, filters: dict = None) -> dict:
        """Get detailed pricing breakdown."""
        if not filters:
            filters = {}

        user = db.query(User).filter(User.id == user_id).first()
        tier = TierConfig.get_tier_config(user.subscription_tier, db)

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
