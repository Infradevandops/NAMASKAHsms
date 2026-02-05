"""Credit management endpoints."""

from datetime import datetime, timezone
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.dependencies import get_current_user_id
from app.core.logging import get_logger
from app.models.user import User
from app.models.transaction import Transaction

logger = get_logger(__name__)
router = APIRouter()


@router.get("/balance")
async def get_credit_balance(
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """Get current credit balance for user."""
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            logger.error(f"User {user_id} not found")
            raise HTTPException(status_code=404, detail="User not found")

        logger.info(f"Retrieved balance for user {user_id}: {user.credits}")

        return {
            "credits": user.credits or 0.0,
            "free_verifications": getattr(user, 'free_verifications', 0),
            "currency": "USD",
            "last_updated": datetime.now(timezone.utc).isoformat()
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get credit balance for user {user_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve balance")


@router.get("/history")
async def get_credit_history(
    user_id: str = Depends(get_current_user_id),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db)
):
    """Get credit transaction history."""
    try:
        transactions = (
            db.query(Transaction)
            .filter(Transaction.user_id == user_id)
            .filter(Transaction.type.in_(["credit", "debit"]))
            .order_by(Transaction.created_at.desc())
            .offset(offset)
            .limit(limit)
            .all()
        )

        total = (
            db.query(Transaction)
            .filter(Transaction.user_id == user_id)
            .filter(Transaction.type.in_(["credit", "debit"]))
            .count()
        )

        return {
            "transactions": [
                {
                    "id": t.id,
                    "type": t.type,
                    "amount": t.amount,
                    "description": t.description,
                    "status": t.status,
                    "created_at": t.created_at.isoformat() if t.created_at else None
                }
                for t in transactions
            ],
            "total": total,
            "limit": limit,
            "offset": offset
        }

    except Exception as e:
        logger.error(f"Failed to get credit history for user {user_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve credit history")


@router.post("/add")
async def add_credits(
    amount: float,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """Add credits to user account (admin only for now)."""
    try:
        if amount <= 0:
            raise HTTPException(status_code=400, detail="Amount must be positive")

        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        # Add credits
        user.credits = (user.credits or 0.0) + amount

        # Create transaction record
        transaction = Transaction(
            user_id=user_id,
            type="credit",
            amount=amount,
            description=f"Manual credit addition",
            status="completed",
            created_at=datetime.now(timezone.utc)
        )

        db.add(transaction)
        db.commit()
        db.refresh(user)

        logger.info(f"Added {amount} credits to user {user_id}")

        return {
            "success": True,
            "amount_added": amount,
            "new_balance": user.credits,
            "transaction_id": transaction.id
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to add credits for user {user_id}: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to add credits")
