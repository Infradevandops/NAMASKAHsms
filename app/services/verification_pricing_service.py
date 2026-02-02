"""Verification service with pricing enforcement."""


from sqlalchemy.orm import Session
from app.models.user import User
from app.services.pricing_calculator import PricingCalculator
from app.services.quota_service import QuotaService

class VerificationPricingService:

    """Handle verification with pricing enforcement."""

    @staticmethod
    def validate_and_calculate_cost(db: Session, user_id: str, filters: dict = None) -> dict:

        """Validate user can purchase and calculate cost."""
        if not filters:
            filters = {}

        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise ValueError("User not found")

        cost_info = PricingCalculator.calculate_sms_cost(db, user_id, filters)

        if not PricingCalculator.validate_balance(db, user_id, cost_info["total_cost"]):
            raise ValueError(f"Insufficient balance. Required: ${cost_info['total_cost']:.2f}")

        return cost_info

        @staticmethod
    def deduct_cost(db: Session, user_id: str, cost: float) -> None:

        """Deduct cost from user balance."""
        user = db.query(User).filter(User.id == user_id).first()

        if user.subscription_tier == "freemium":
            user.bonus_sms_balance -= 1
        else:
            user.credits -= cost

        QuotaService.add_quota_usage(db, user_id, cost)
        db.commit()

        @staticmethod
    def get_pricing_breakdown(db: Session, user_id: str, filters: dict = None) -> dict:

        """Get pricing breakdown for user."""
        return PricingCalculator.get_pricing_breakdown(db, user_id, filters)