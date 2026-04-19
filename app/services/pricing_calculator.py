"""Pricing calculation service.

v4.5.0: Provider-price-driven billing.
The base cost for every purchase is now derived from the ACTUAL provider price
(TextVerified, Telnyx, etc.) × the platform markup.  The old hardcoded
`base_sms_cost` from tier config is used ONLY as a last-resort fallback when
the provider price is unavailable.
"""

from sqlalchemy.orm import Session

from app.core.config import get_settings
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
    def _resolve_base_cost(
        provider_price: float = None, tier: dict = None
    ) -> tuple:
        """Return (base_cost, price_source) using provider price when available.

        Priority:
          1. provider_price × markup  (real cost from TextVerified / other provider)
          2. tier["base_sms_cost"]    (hardcoded fallback — legacy)
        """
        settings = get_settings()
        if provider_price is not None and provider_price > 0:
            return round(provider_price * settings.price_markup, 2), "provider"
        fallback = tier.get("base_sms_cost", 2.50) if tier else 2.50
        return fallback, "fallback"

    @staticmethod
    def calculate_sms_cost(
        db: Session,
        user_id: str,
        filters: dict = None,
        provider_price: float = None,
    ) -> dict:
        """Calculate total cost for SMS verification.

        Args:
            provider_price: The raw cost the provider (e.g. TextVerified) charges
                            for this specific service.  When supplied the user is
                            billed provider_price × markup instead of the static
                            tier base_sms_cost.
        """
        if not filters:
            filters = {}

        user = db.query(User).filter(User.id == user_id).first()
        tier_name = user.subscription_tier
        tier = TierConfig.get_tier_config(tier_name, db)

        base_cost, price_source = PricingCalculator._resolve_base_cost(
            provider_price, tier
        )

        if base_cost is None or base_cost <= 0:
            raise ValueError(
                f"Cannot purchase SMS: base cost is not configured for tier '{tier_name}'. "
                "Please contact support."
            )

        # Track individual surcharges (v4.4.1)
        carrier_premium = 0.0
        area_code_premium = 0.0

        if tier_name == "payg":
            ac = filters.get("area_code")
            if ac:
                area_code_premium = PricingCalculator.AREA_CODE_PREMIUMS.get(
                    str(ac), 0.25
                )
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
        total_cost = round(base_cost + filter_charges + overage_charge, 2)

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
            "carrier_surcharge": carrier_premium,
            "area_code_surcharge": area_code_premium,
            "price_source": price_source,
            "provider_cost": provider_price,
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
        """Check if user has sufficient balance."""
        user = db.query(User).filter(User.id == user_id).first()
        resolved_tier = tier or user.subscription_tier

        if resolved_tier == "freemium":
            return user.bonus_sms_balance >= 1

        if resolved_tier in ("pro", "custom"):
            usage = QuotaService.get_monthly_usage(db, user_id, tier=resolved_tier)
            quota_remaining = usage["remaining"]
            if quota_remaining >= cost:
                return True
            overage = QuotaService.calculate_overage(
                db, user_id, cost, tier=resolved_tier
            )
            return user.credits >= overage

        return user.credits >= cost

    @staticmethod
    def get_pricing_breakdown(
        db: Session, user_id: str, filters: dict = None, provider_price: float = None
    ) -> dict:
        """Get detailed pricing breakdown."""
        if not filters:
            filters = {}

        user = db.query(User).filter(User.id == user_id).first()
        tier = TierConfig.get_tier_config(user.subscription_tier, db)

        cost_info = PricingCalculator.calculate_sms_cost(
            db, user_id, filters, provider_price=provider_price
        )
        quota_info = QuotaService.get_monthly_usage(db, user_id)

        return {
            "tier": user.subscription_tier,
            "tier_name": tier.get("name", "Unknown"),
            "base_cost": cost_info["base_cost"],
            "filter_charges": cost_info["filter_charges"],
            "overage_charge": cost_info["overage_charge"],
            "total_cost": cost_info["total_cost"],
            "price_source": cost_info["price_source"],
            "provider_cost": cost_info["provider_cost"],
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

    @staticmethod
    def calculate_rental_cost(
        db: Session,
        user_id: str,
        duration_hours: float,
        provider_cost: float = None,
    ) -> dict:
        """Calculate total cost for number rental.

        Args:
            provider_cost: Actual cost returned by the provider for this
                           reservation.  When available, the user is charged
                           provider_cost × markup.  Falls back to $0.25/hr.
        """
        settings = get_settings()

        if provider_cost is not None and provider_cost > 0:
            total_cost = round(provider_cost * settings.price_markup, 2)
            return {
                "total_cost": total_cost,
                "duration_hours": duration_hours,
                "hourly_rate": round(total_cost / max(duration_hours, 1), 4),
                "price_source": "provider",
                "provider_cost": provider_cost,
            }

        # Fallback: flat hourly rate
        hourly_rate = 0.25
        total_cost = round(hourly_rate * duration_hours, 2)
        return {
            "total_cost": total_cost,
            "duration_hours": duration_hours,
            "hourly_rate": hourly_rate,
            "price_source": "fallback",
            "provider_cost": None,
        }
