"""User-facing dispute endpoints."""

import logging

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user_id
from app.services.dispute_service import DisputeService

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/disputes", tags=["Disputes"])


class OpenDisputeRequest(BaseModel):
    payment_id: str
    reason_code: str
    reason_description: str
    amount: float


@router.post("/open")
async def open_dispute(
    payload: OpenDisputeRequest,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Open a payment dispute."""
    try:
        service = DisputeService(db)
        try:
            return await service.open_dispute(
                user_id=user_id,
                payment_id=payload.payment_id,
                reason_code=payload.reason_code,
                reason_description=payload.reason_description,
                amount=payload.amount,
            )
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error opening dispute for user {user_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to open dispute")


@router.get("/my")
async def get_my_disputes(
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Get current user's open disputes."""
    try:
        service = DisputeService(db)
        return await service.get_open_disputes(user_id=user_id)
    except Exception as e:
        logger.error(f"Error fetching disputes for user {user_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to fetch disputes")
