"""Auto-topup service for low balance management."""

from typing import Optional
from sqlalchemy.orm import Session
from app.models.user import User
from app.models.user_preference import UserPreference
from app.services.payment_service import PaymentService


class AutoTopupService:
    """Automatic credit top-up when balance is low."""

    def __init__(self, db: Session):
        self.db = db
        self.payment_service = PaymentService(db)

    async def check_and_topup(self, user_id: str) -> Optional[dict]:
        """Check if user needs auto-topup and initiate if enabled."""
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            return None

        pref = self.db.query(UserPreference).filter(UserPreference.user_id == user_id).first()
        if not pref or not pref.auto_recharge:
            return None

        threshold = pref.auto_recharge_threshold or 5.0
        if (user.credits or 0) > threshold:
            return None

        if not pref.paystack_authorization_code:
            return {"status": "skipped", "reason": "no_card_on_file"}

        topup_amount = pref.recharge_amount or 10.0

        try:
            result = await self.payment_service.initialize_payment(
                user_id=user_id,
                email=user.email,
                amount_usd=topup_amount,
                metadata={"auto_recharge": True},
            )
            return {
                "status": "initiated",
                "amount": topup_amount,
                "payment_url": result.get("authorization_url"),
                "reference": result.get("reference"),
            }
        except Exception as e:
            return {"status": "failed", "error": str(e)}

    def enable_auto_topup(self, user_id: str, amount: float = 10.0, threshold: float = 5.0) -> bool:
        pref = self.db.query(UserPreference).filter(UserPreference.user_id == user_id).first()
        if not pref:
            pref = UserPreference(user_id=user_id)
            self.db.add(pref)
        pref.auto_recharge = True
        pref.recharge_amount = amount
        pref.auto_recharge_threshold = threshold
        self.db.commit()
        return True

    def disable_auto_topup(self, user_id: str) -> bool:
        pref = self.db.query(UserPreference).filter(UserPreference.user_id == user_id).first()
        if pref:
            pref.auto_recharge = False
            self.db.commit()
        return True
