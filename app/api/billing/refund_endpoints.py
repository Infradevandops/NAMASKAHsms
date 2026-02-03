"""Refund endpoints for billing operations."""

from datetime import datetime, timezone
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.dependencies import get_current_user_id
from app.core.logging import get_logger
from app.models.user import User
from app.models.transaction import Transaction
from app.schemas.payment import RefundRequest, RefundResponse

logger = get_logger(__name__)
router = APIRouter()


@router.post("/request", response_model=RefundResponse)
async def request_refund(
    refund_data: RefundRequest,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """Request a refund for a transaction."""
    try:
        # Find the transaction
        transaction = (
            db.query(Transaction)
            .filter(Transaction.id == refund_data.transaction_id)
            .filter(Transaction.user_id == user_id)
            .first()
        )

        if not transaction:
            raise HTTPException(status_code=404, detail="Transaction not found")

        if transaction.type != "debit":
            raise HTTPException(status_code=400, detail="Only debit transactions can be refunded")

        # Create refund record (simplified)
        refund_amount = refund_data.amount or abs(transaction.amount)
        
        refund_id = f"refund_{int(datetime.now().timestamp())}"

        return RefundResponse(
            refund_id=refund_id,
            status="pending",
            amount=refund_amount,
            reason=refund_data.reason,
            processed_at=None
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to request refund for user {user_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to process refund request")


@router.get("/status/{refund_id}")
async def get_refund_status(
    refund_id: str,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """Get status of a refund request."""
    try:
        # For now, return a basic status since we don't have a refund model
        return {
            "refund_id": refund_id,
            "status": "pending",
            "message": "Refund is being processed",
            "estimated_completion": "2-3 business days"
        }

    except Exception as e:
        logger.error(f"Failed to get refund status for user {user_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve refund status")


@router.get("/history")
async def get_refund_history(
    user_id: str = Depends(get_current_user_id),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db)
):
    """Get refund history for user."""
    try:
        # For now, return empty history since we don't have a refund model
        return {
            "refunds": [],
            "total": 0,
            "limit": limit,
            "offset": offset
        }

    except Exception as e:
        logger.error(f"Failed to get refund history for user {user_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve refund history")