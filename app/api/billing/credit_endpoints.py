"""Credit management endpoints."""

from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user_id
from app.core.logging import get_logger
from app.models.transaction import Transaction
from app.models.user import User

logger = get_logger(__name__)
router = APIRouter()

# Module-level singleton — avoids rebuilding the HTTP client on every request
_tv_service = None


def _get_tv_service():
    global _tv_service
    if _tv_service is None:
        from app.services.textverified_service import TextVerifiedService

        _tv_service = TextVerifiedService()
    return _tv_service


@router.get("/balance")
async def get_credit_balance(
    user_id: str = Depends(get_current_user_id), db: Session = Depends(get_db)
):
    """Get current credit balance. For admin, returns TextVerified API balance."""
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        if user.is_admin:
            from app.core.unified_cache import cache

            _BALANCE_CACHE_KEY = "tv:admin_balance"
            cached = await cache.get(_BALANCE_CACHE_KEY)
            if cached is not None:
                balance = cached
            else:
                bal_data = await _get_tv_service().get_balance()
                balance = bal_data.get("balance", 0.0)
                await cache.set(_BALANCE_CACHE_KEY, balance, ttl=60)
                logger.info(
                    f"Retrieved TextVerified balance for admin {user_id}: {balance}"
                )
            return {
                "credits": balance,
                "free_verifications": getattr(user, "free_verifications", 0),
                "currency": "USD",
                "source": "textverified",
                "last_updated": datetime.now(timezone.utc).isoformat(),
            }

        logger.info(f"Retrieved balance for user {user_id}: {user.credits}")
        return {
            "credits": user.credits or 0.0,
            "free_verifications": getattr(user, "free_verifications", 0),
            "currency": "USD",
            "last_updated": datetime.now(timezone.utc).isoformat(),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get credit balance for user {user_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve balance")


@router.post("/add")
async def add_credits(
    amount: float,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Add credits to user account (admin only for now)."""
    try:
        if amount <= 0:
            raise HTTPException(status_code=400, detail="Amount must be positive")

        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        # Use CreditService for consistent auditing
        from app.services.credit_service import CreditService

        credit_service = CreditService(db)
        result = credit_service.add_credits(
            user_id=user_id,
            amount=amount,
            description="Manual credit addition",
            transaction_type="credit",
        )

        return {
            "success": True,
            "amount_added": amount,
            "new_balance": result["new_balance"],
            "transaction_id": result.get(
                "transaction_id"
            ),  # Note: result has transaction keys
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to add credits for user {user_id}: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to add credits")
