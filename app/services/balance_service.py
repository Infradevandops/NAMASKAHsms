"""Balance management service with dual-mode support."""

from datetime import datetime, timezone
from typing import Any, Dict

from sqlalchemy.orm import Session

from app.core.logging import get_logger
from app.models.user import User
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
            # Admin: Always fetch from TextVerified
            try:
                tv_service = TextVerifiedService()
                if not tv_service.enabled:
                    logger.warning("TextVerified service not enabled for admin")
                    return {
                        "balance": user.credits,
                        "source": "cached",
                        "is_admin": True,
                        "error": "TextVerified service not configured",
                        "last_synced": getattr(user, "balance_last_synced", None),
                    }

                tv_balance = await tv_service.get_balance()
                live_balance = tv_balance.get("balance", 0.0)

                # Update local cache for analytics
                user.credits = live_balance
                user.balance_last_synced = datetime.now(timezone.utc)
                db.commit()

                logger.info(f"Admin balance synced: ${live_balance:.2f}")

                return {
                    "balance": live_balance,
                    "source": "textverified",
                    "is_admin": True,
                    "last_synced": user.balance_last_synced,
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
