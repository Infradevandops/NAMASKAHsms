"""Verification service with pricing enforcement."""

from sqlalchemy.orm import Session

from app.models.user import User
from app.services.pricing_calculator import PricingCalculator
from app.services.quota_service import QuotaService


class VerificationPricingService:
    """Handle verification with pricing enforcement."""

    @staticmethod
    def validate_and_calculate_cost(
        db: Session, user_id: str, filters: dict = None
    ) -> dict:
        """Validate user can purchase and calculate cost."""
        if not filters:
            filters = {}

        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise ValueError("User not found")

        cost_info = PricingCalculator.calculate_sms_cost(db, user_id, filters)

        if not PricingCalculator.validate_balance(db, user_id, cost_info["total_cost"]):
            raise ValueError(
                f"Insufficient balance. Required: ${cost_info['total_cost']:.2f}"
            )

        return cost_info

    @staticmethod
    def deduct_cost(db: Session, user_id: str, cost: float, tier: str = None) -> None:
        """Deduct cost from user balance.

        - freemium: deduct 1 from bonus_sms_balance
        - payg: deduct full cost from credits
        - pro/custom: only deduct the overage portion from credits;
          within-quota usage is tracked by QuotaService only.
        """
        user = db.query(User).filter(User.id == user_id).first()
        resolved_tier = tier or user.subscription_tier

        description = "SMS Verification"
        credits_deducted = 0.0

        if resolved_tier == "freemium":
            user.bonus_sms_balance -= 1
            description = "SMS Verification (Bonus Balance)"
        elif resolved_tier in ("pro", "custom"):
            overage = QuotaService.calculate_overage(
                db, user_id, cost, tier=resolved_tier
            )
            if overage > 0:
                user.credits = float(user.credits) - overage
                credits_deducted = overage
                description = f"SMS Verification (Overage: ${overage:.2f})"
            else:
                description = "SMS Verification (Within Quota)"
        else:
            # payg
            user.credits = float(user.credits) - cost
            credits_deducted = cost
            description = f"SMS Verification (${cost:.2f})"

        # Create main records if credits were actually taken
        if credits_deducted > 0:
            from datetime import datetime, timezone

            from app.core.constants import TransactionType
            from app.models.balance_transaction import BalanceTransaction
            from app.models.transaction import Transaction

            tx = Transaction(
                user_id=user_id,
                amount=-credits_deducted,
                type="sms_purchase",
                description=description,
                status="completed",
                created_at=datetime.now(timezone.utc),
            )
            db.add(tx)

            balance_tx = BalanceTransaction(
                user_id=user_id,
                amount=-credits_deducted,
                type=TransactionType.DEBIT,
                description=description,
                balance_after=float(user.credits),
                created_at=datetime.now(timezone.utc),
            )
            db.add(balance_tx)

        QuotaService.add_quota_usage(db, user_id, cost)
        db.commit()

    @staticmethod
    def get_pricing_breakdown(db: Session, user_id: str, filters: dict = None) -> dict:
        """Get pricing breakdown for user."""
        return PricingCalculator.get_pricing_breakdown(db, user_id, filters)
