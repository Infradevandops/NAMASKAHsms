"""Auto-topup service for low balance management."""

import secrets
from typing import Optional

from sqlalchemy.orm import Session

from app.models.transaction import PaymentLog
from app.models.user import User
from app.models.user_preference import UserPreference
from app.services.paystack_service import PaystackService


class AutoTopupService:
    """Automatic credit top-up when balance is low."""

    def __init__(self, db: Session):
        self.db = db
        self.paystack = PaystackService()

    async def check_and_topup(self, user_id: str) -> Optional[dict]:
        """Charge saved card if balance is below threshold and auto-recharge is enabled."""
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            return None

        pref = (
            self.db.query(UserPreference)
            .filter(UserPreference.user_id == user_id)
            .first()
        )
        if not pref or not pref.auto_recharge:
            return None

        threshold = pref.auto_recharge_threshold or 5.0
        if (user.credits or 0) > threshold:
            return None

        if not pref.paystack_authorization_code:
            return {"status": "skipped", "reason": "no_card_on_file"}

        topup_amount = pref.recharge_amount or 10.0
        reference = f"auto_{user_id[:8]}_{secrets.token_hex(6)}"

        try:
            result = await self.paystack.charge_authorization(
                authorization_code=pref.paystack_authorization_code,
                email=user.email,
                amount_usd=topup_amount,
                reference=reference,
                metadata={"auto_recharge": True, "user_id": user_id},
            )

            # Credit the user immediately on success
            log = PaymentLog(
                user_id=user_id,
                email=user.email,
                reference=reference,
                amount_usd=topup_amount,
                namaskah_amount=topup_amount,
                status="success",
                credited=True,
                state="completed",
            )
            self.db.add(log)
            user.credits = type(user.credits)(float(user.credits) + topup_amount)

            # Record in main Transaction table (Analytics)
            from datetime import datetime, timezone

            from app.models.transaction import Transaction

            transaction = Transaction(
                user_id=user_id,
                reference=reference,
                type="credit",
                amount=topup_amount,
                description=f"Auto-recharge via saved card ({reference})",
                status="completed",
                created_at=datetime.now(timezone.utc),
            )
            self.db.add(transaction)

            # Record in BalanceTransaction (Strict Audit)
            from app.core.constants import TransactionType
            from app.models.balance_transaction import BalanceTransaction

            balance_tx = BalanceTransaction(
                user_id=user_id,
                amount=topup_amount,
                type=TransactionType.CREDIT,
                description=f"Auto-Topup: {reference}",
                balance_after=float(user.credits),
                created_at=datetime.now(timezone.utc),
            )
            self.db.add(balance_tx)

            self.db.commit()

            # Notify user
            try:
                from app.services.notification_dispatcher import NotificationDispatcher

                dispatcher = NotificationDispatcher(self.db)
                import asyncio

                asyncio.create_task(
                    dispatcher.notify_payment_completed(
                        user_id=user_id,
                        amount=topup_amount,
                        new_balance=float(user.credits),
                    )
                )
            except Exception:
                pass

            return {"status": "success", "amount": topup_amount, "reference": reference}

        except Exception as e:
            return {"status": "failed", "error": str(e)}

    def enable_auto_topup(
        self, user_id: str, amount: float = 10.0, threshold: float = 5.0
    ) -> bool:
        pref = (
            self.db.query(UserPreference)
            .filter(UserPreference.user_id == user_id)
            .first()
        )
        if not pref:
            pref = UserPreference(user_id=user_id)
            self.db.add(pref)
        pref.auto_recharge = True
        pref.recharge_amount = amount
        pref.auto_recharge_threshold = threshold
        self.db.commit()
        return True

    def disable_auto_topup(self, user_id: str) -> bool:
        pref = (
            self.db.query(UserPreference)
            .filter(UserPreference.user_id == user_id)
            .first()
        )
        if pref:
            pref.auto_recharge = False
            self.db.commit()
        return True
