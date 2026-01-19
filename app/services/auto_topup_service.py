"""Auto - topup service for low balance management."""

from typing import Optional

from sqlalchemy.orm import Session

from app.models.user import User
from app.services.payment_service import PaymentService


class AutoTopupService:
    """Automatic credit top - up when balance is low."""

    def __init__(self, db: Session):
        self.db = db
        self.payment_service = PaymentService(db)
        self.low_balance_threshold = 2.0  # Credits
        self.default_topup_amount = 25.0  # USD

    async def check_and_topup(self, user_id: str) -> Optional[dict]:
        """Check if user needs auto - topup and initiate if enabled."""
        user = self.db.query(User).filter(User.id == user_id).first()

        if not user or not hasattr(user, "auto_topup_enabled"):
            return None

        # Check if balance is below threshold
        if user.credits > self.low_balance_threshold:
            return None

        # Check if auto - topup is enabled for user
        if not getattr(user, "auto_topup_enabled", False):
            return None

        # Get user's preferred topup amount
        topup_amount = getattr(user, "auto_topup_amount", self.default_topup_amount)

        try:
            # Initialize payment for auto - topup
            result = await self.payment_service.initialize_payment(
                user_id=user_id,
                email=user.email,
                amount_usd=topup_amount,
                auto_topup=True,
            )

            return {
                "status": "initiated",
                "amount": topup_amount,
                "payment_url": result.get("authorization_url"),
                "reference": result.get("reference"),
            }

        except Exception as e:
            return {"status": "failed", "error": str(e)}

    def enable_auto_topup(self, user_id: str, amount: float = 25.0) -> bool:
        """Enable auto - topup for user."""
        user = self.db.query(User).filter(User.id == user_id).first()

        if not user:
            return False

        # Add auto - topup fields (would need migration in production)
        user.auto_topup_enabled = True
        user.auto_topup_amount = amount

        self.db.commit()
        return True

    def disable_auto_topup(self, user_id: str) -> bool:
        """Disable auto - topup for user."""
        user = self.db.query(User).filter(User.id == user_id).first()

        if not user:
            return False

        user.auto_topup_enabled = False
        self.db.commit()
        return True
