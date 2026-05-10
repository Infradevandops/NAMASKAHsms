"""Pricing calculation service.

v5.0: Clean pricing model.
  provider_price × markup = platform_price

No fallbacks. If the provider price is unknown, the purchase is blocked.
"""

from decimal import Decimal
from typing import Optional

from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.tier_config import TierConfig
from app.models.user import User
from app.services.pricing_template_service import PricingTemplateService
from app.services.quota_service import QuotaService


class PricingCalculator:
    """Calculate verification costs from real provider prices."""

    @staticmethod
    def calculate_sms_cost(
        db: Session,
        user_id: str,
        filters: Optional[dict] = None,
        provider_price: Optional[float] = None,
    ) -> dict:
        """Calculate total cost for SMS/voice verification.

        Args:
            provider_price: Raw cost from the provider (e.g. TextVerified)
                            for this specific service. Required for purchase.
        """
        if not filters:
            filters = {}

        # Provider price is the single source of truth
        if provider_price is None or provider_price <= 0:
            raise ValueError(
                "Cannot calculate price: provider price unavailable for this service. "
                "Please try again or contact support."
            )

        user = db.query(User).filter(User.id == user_id).first()
        tier_name = user.subscription_tier

        settings = get_settings()

        # Try to get markup from active pricing template
        markup = Decimal(str(settings.price_markup))
        try:
            pt_service = PricingTemplateService(db)
            active_template = pt_service.get_active_template()
            if active_template and hasattr(active_template, "markup_multiplier"):
                markup = active_template.markup_multiplier
                if getattr(active_template, "is_promotional", False) and getattr(
                    active_template, "discount_percentage", 0
                ):
                    discount = Decimal(str(active_template.discount_percentage))
                    markup = markup * (1 - discount / 100)
        except Exception as e:
            from app.core.logging import get_logger

            get_logger(__name__).warning(f"Failed to get active template markup: {e}")

        from decimal import Decimal

        base_cost = round(float(Decimal(str(provider_price)) * markup), 2)

        if tier_name == "freemium" and any(filters.values()):
            raise ValueError("Filters not available for Freemium tier")

        overage_charge = QuotaService.calculate_overage(
            db, user_id, base_cost, tier=tier_name
        )
        total_cost = round(base_cost + overage_charge, 2)

        return {
            "base_cost": base_cost,
            "overage_charge": overage_charge,
            "total_cost": total_cost,
            "tier": tier_name,
            "provider_cost": provider_price,
            "markup": float(markup),
        }

    @staticmethod
    def calculate_voice_cost(
        db: Session,
        user_id: str,
        provider_price: Optional[float] = None,
        area_code: Optional[str] = None,
    ) -> dict:
        """Calculate voice verification cost with area code tier gating."""
        if provider_price is None or provider_price <= 0:
            raise ValueError("Provider price required")

        user = db.query(User).filter(User.id == user_id).first()
        tier_name = user.subscription_tier

        from app.models.subscription_tier import SubscriptionTier

        tier_config = (
            db.query(SubscriptionTier)
            .filter(SubscriptionTier.tier == tier_name)
            .first()
        )

        if area_code:
            if tier_name == "freemium":
                raise ValueError("Area code selection not available for Freemium tier")
            if tier_name == "payg" and (
                not tier_config or not tier_config.has_area_code_selection
            ):
                raise ValueError("Area code selection requires Pro tier or higher")

        settings = get_settings()
        markup = Decimal(str(settings.price_markup))
        try:
            pt_service = PricingTemplateService(db)
            active_template = pt_service.get_active_template()
            if active_template and hasattr(active_template, "markup_multiplier"):
                markup = active_template.markup_multiplier
                if getattr(active_template, "is_promotional", False) and getattr(
                    active_template, "discount_percentage", 0
                ):
                    discount = Decimal(str(active_template.discount_percentage))
                    markup = markup * (1 - discount / 100)
        except Exception:
            pass

        base_cost = round(float(Decimal(str(provider_price)) * markup), 2)
        area_code_fee = 0.0

        if area_code and tier_name == "payg":
            area_code_fee = 0.25

        overage_charge = QuotaService.calculate_overage(
            db, user_id, base_cost, tier=tier_name
        )
        total_cost = round(base_cost + area_code_fee + overage_charge, 2)

        return {
            "base_cost": base_cost,
            "area_code_fee": area_code_fee,
            "overage_charge": overage_charge,
            "total_cost": total_cost,
            "tier": tier_name,
            "provider_cost": provider_price,
            "markup": float(markup),
        }

    @staticmethod
    def calculate_rental_cost(
        db: Session,
        user_id: str,
        duration_hours: float,
        provider_cost: Optional[float] = None,
        area_code: Optional[str] = None,
    ) -> dict:
        """Calculate rental cost with area code tier gating."""
        if provider_cost is None or provider_cost <= 0:
            raise ValueError("Provider cost required")

        user = db.query(User).filter(User.id == user_id).first()
        tier_name = user.subscription_tier

        from app.models.subscription_tier import SubscriptionTier

        tier_config = (
            db.query(SubscriptionTier)
            .filter(SubscriptionTier.tier == tier_name)
            .first()
        )

        if area_code:
            if tier_name == "freemium":
                raise ValueError("Area code selection not available for Freemium tier")
            if tier_name == "payg" and (
                not tier_config or not tier_config.has_area_code_selection
            ):
                raise ValueError("Area code selection requires Pro tier or higher")

        settings = get_settings()
        markup = Decimal(str(settings.price_markup))
        try:
            pt_service = PricingTemplateService(db)
            active_template = pt_service.get_active_template()
            if active_template and hasattr(active_template, "markup_multiplier"):
                markup = active_template.markup_multiplier
                if getattr(active_template, "is_promotional", False) and getattr(
                    active_template, "discount_percentage", 0
                ):
                    discount = Decimal(str(active_template.discount_percentage))
                    markup = markup * (1 - discount / 100)
        except Exception:
            pass

        base_cost = round(float(Decimal(str(provider_cost)) * markup), 2)
        area_code_fee = 0.0

        if area_code and tier_name == "payg":
            area_code_fee = 0.50

        total_cost = round(base_cost + area_code_fee, 2)

        return {
            "total_cost": total_cost,
            "base_cost": base_cost,
            "area_code_fee": area_code_fee,
            "duration_hours": duration_hours,
            "provider_cost": provider_cost,
            "markup": float(markup),
        }

    @staticmethod
    def validate_balance(
        db: Session, user_id: str, cost: float, tier: Optional[str] = None
    ) -> bool:
        """Check if user has sufficient balance.

        - Freemium/PAYG: needs credits >= cost
        - Pro/Custom within quota: always passes (subscription covers it)
        - Pro/Custom over quota: needs credits >= overage portion
        """
        user = db.query(User).filter(User.id == user_id).first()
        resolved_tier = tier or user.subscription_tier

        if resolved_tier in ("pro", "custom"):
            overage = QuotaService.calculate_overage(
                db, user_id, cost, tier=resolved_tier
            )
            if overage <= 0:
                return True  # within quota, subscription covers it
            return user.credits >= overage

        return user.credits >= cost

    @staticmethod
    def get_pricing_breakdown(
        db: Session,
        user_id: str,
        filters: Optional[dict] = None,
        provider_price: Optional[float] = None,
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
            "overage_charge": cost_info["overage_charge"],
            "total_cost": cost_info["total_cost"],
            "provider_cost": cost_info["provider_cost"],
            "markup": cost_info["markup"],
            "quota_limit": quota_info["quota_limit"],
            "quota_used": quota_info["quota_used"],
            "quota_remaining": quota_info["remaining"],
            "user_balance": user.credits,
            "sufficient_balance": PricingCalculator.validate_balance(
                db, user_id, cost_info["total_cost"]
            ),
        }
