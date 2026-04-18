"""Payment history endpoints."""

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


@router.get("/history")
async def get_payment_history(
    user_id: str = Depends(get_current_user_id),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    transaction_type: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    """Get payment history for user."""
    try:
        from app.models.balance_transaction import BalanceTransaction
        
        query = db.query(BalanceTransaction).filter(BalanceTransaction.user_id == user_id)

        if transaction_type:
            query = query.filter(BalanceTransaction.type == transaction_type)

        total = query.count()
        balance_txs = (
            query.order_by(BalanceTransaction.created_at.desc())
            .offset(offset)
            .limit(limit)
            .all()
        )

        return {
            "transactions": [
                {
                    "id": bt.id,
                    "type": bt.type,
                    "amount": float(bt.amount),
                    "description": bt.description,
                    "balance_after": float(bt.balance_after or 0.0),
                    "status": "completed", # Balance transactions are by definition completed
                    "created_at": bt.created_at.isoformat() if bt.created_at else None,
                    "reference": bt.id[:8], # Use prefix as short reference if needed
                }
                for bt in balance_txs
            ],
            "total": total,
            "limit": limit,
            "offset": offset,
        }

    except Exception as e:
        logger.error(f"Failed to get payment history for user {user_id}: {e}")
        raise HTTPException(
            status_code=500, detail="Failed to retrieve payment history"
        )


@router.get("/summary")
async def get_payment_summary(
    user_id: str = Depends(get_current_user_id),
    days: int = Query(30, ge=1, le=365),
    db: Session = Depends(get_db),
):
    """Get payment summary for user."""
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        # Get basic summary
        total_credits = (
            db.query(Transaction)
            .filter(Transaction.user_id == user_id)
            .filter(Transaction.type == "credit")
            .count()
        )

        total_debits = (
            db.query(Transaction)
            .filter(Transaction.user_id == user_id)
            .filter(Transaction.type == "debit")
            .count()
        )

        return {
            "current_balance": user.credits or 0.0,
            "total_credits": total_credits,
            "total_debits": total_debits,
            "summary_period_days": days,
            "last_updated": datetime.now(timezone.utc).isoformat(),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get payment summary for user {user_id}: {e}")
        raise HTTPException(
            status_code=500, detail="Failed to retrieve payment summary"
        )
