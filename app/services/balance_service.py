"""Balance management service with dual-mode support."""

from datetime import datetime, timezone
from typing import Any, Dict, Optional, Tuple

from sqlalchemy.orm import Session

from app.core.logging import get_logger
from app.models.user import User
from app.models.verification import Verification
from app.services.textverified_service import TextVerifiedService

logger = get_logger(__name__)


class BalanceService:
    """Unified balance service for admin and regular users."""

    @staticmethod
    async def get_user_balance(user_id: str, db: Session) -> Dict[str, Any]:
        """Get user balance with source tracking.

        Returns:
            {
                "balance": float,
                "source": "textverified" | "local" | "cached",
                "is_admin": bool,
                "last_synced": datetime (admin only),
                "error": str (if sync failed)
            }
        """
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise ValueError("User not found")

        if user.is_admin:
            # Admin: Always fetch from TextVerified with row-level locking for sync
            try:
                # Use a fresh lock-protected query for the update phase
                admin_user = db.query(User).filter(User.id == user_id).with_for_update().first()
                if not admin_user:
                    raise ValueError("Admin user lost during sync")

                tv_service = TextVerifiedService()
                if not tv_service.enabled:
                    logger.warning("TextVerified service not enabled for admin")
                    return {
                        "balance": float(admin_user.credits),
                        "source": "cached",
                        "is_admin": True,
                        "error": "TextVerified service not configured",
                        "last_synced": getattr(admin_user, "balance_last_synced", None),
                    }

                tv_balance = await tv_service.get_balance()
                live_balance = tv_balance.get("balance", 0.0)

                # Update local cache for analytics atomically
                admin_user.credits = live_balance
                admin_user.balance_last_synced = datetime.now(timezone.utc)
                db.commit()

                logger.info(f"Admin balance sync-locked: ${live_balance:.2f}")

                return {
                    "balance": live_balance,
                    "source": "textverified",
                    "is_admin": True,
                    "last_synced": admin_user.balance_last_synced,
                }
            except Exception as e:
                logger.error(f"TextVerified balance fetch failed: {e}")
                # Fallback to cached value with warning
                return {
                    "balance": float(user.credits),
                    "source": "cached",
                    "is_admin": True,
                    "error": str(e),
                    "last_synced": getattr(user, "balance_last_synced", None),
                }
        else:
            # Regular user: Use local balance
            return {
                "balance": float(user.credits),
                "source": "local",
                "is_admin": False,
            }

    @staticmethod
    async def check_sufficient_balance(
        user_id: str, required_amount: float, db: Session
    ) -> Dict[str, Any]:
        """Check if user has sufficient balance.

        Returns:
            {
                "sufficient": bool,
                "current_balance": float,
                "required": float,
                "shortfall": float (if insufficient),
                "source": str
            }
        """
        balance_info = await BalanceService.get_user_balance(user_id, db)
        current_balance = balance_info["balance"]
        sufficient = current_balance >= required_amount

        result = {
            "sufficient": sufficient,
            "current_balance": current_balance,
            "required": required_amount,
            "source": balance_info["source"],
        }

        if not sufficient:
            result["shortfall"] = required_amount - current_balance

        return result

    @staticmethod
    def deduct_credits_for_verification(
        db: Session,
        user: User,
        verification: Verification,
        cost: float,
        service_name: str,
        country_code: str,
    ) -> Tuple[bool, Optional[str]]:
        """Deduct credits and create transaction records.

        Returns:
            Tuple of (success: bool, error_message: Optional[str])
        """
        import uuid

        from app.core.constants import FailureReason, TransactionType
        from app.models.balance_transaction import BalanceTransaction
        from app.models.transaction import Transaction
        from app.services.verification_status_service import mark_verification_failed

        # Check sufficient balance
        if float(user.credits) < cost:
            mark_verification_failed(
                db,
                verification,
                reason=FailureReason.INSUFFICIENT_BALANCE,
                error_message=f"Insufficient balance. Required: ${cost:.2f}, Available: ${user.credits:.2f}",
                refund_eligible=False,
            )
            return False, "Insufficient balance"

        try:
            # Update user credits
            old_balance = float(user.credits)
            user.credits -= type(user.credits)(cost)
            new_balance = float(user.credits)

            # 1. Create BalanceTransaction (for accounting)
            balance_tx = BalanceTransaction(
                id=str(uuid.uuid4()),
                user_id=user.id,
                amount=-abs(cost),
                type=TransactionType.DEBIT,
                description=f"SMS: {service_name} ({country_code})",
                balance_after=new_balance,
                created_at=datetime.now(timezone.utc),
            )
            db.add(balance_tx)

            # 2. Create Transaction (for analytics/history - Legacy Parity)
            transaction = Transaction(
                id=str(uuid.uuid4()),
                user_id=user.id,
                amount=-abs(cost),
                type="sms_purchase",
                description=f"SMS verification for {service_name}",
                service=service_name,
                status="completed",
                reference=f"sms_{verification.id}",
                created_at=datetime.now(timezone.utc),
            )
            db.add(transaction)

            # Fix: Ensure verification points to the audit ledger
            verification.debit_transaction_id = balance_tx.id
            
            # Atomic Sync: Mirror IDs for parity
            transaction.payment_log_id = balance_tx.id

            # Use flush instead of commit to allow caller to manage the transaction boundary
            db.flush()
            logger.info(
                f"Ledger Synced for {user.id}: -${cost:.2f} (Ref: {verification.id})"
            )

            # Notifications
            try:
                import asyncio

                from app.services.notification_dispatcher import NotificationDispatcher

                dispatcher = NotificationDispatcher(db)
                # 1. Notify balance update
                asyncio.create_task(
                    dispatcher.notify_balance_deducted(
                        user_id=user.id,
                        amount=cost,
                        service=service_name,
                        new_balance=new_balance,
                    )
                )
                # 2. Notify verification started
                asyncio.create_task(
                    dispatcher.notify_verification_started(
                        user_id=user.id,
                        verification_id=str(verification.id),
                        service=service_name,
                        phone_number=verification.phone_number or "assigned number",
                        cost=cost,
                    )
                )
            except Exception as e:
                logger.error(f"Failed to send verification notifications: {e}")

            return True, None

        except Exception as e:
            db.rollback()
            logger.error(f"Credit deduction failed for {user.id}: {e}")
            mark_verification_failed(
                db,
                verification,
                reason=FailureReason.DATABASE_ERROR,
                error_message=f"Transaction logging failed: {str(e)}",
                refund_eligible=True,
            )
            return False, str(e)
