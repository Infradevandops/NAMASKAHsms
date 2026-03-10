"""Record verification outcome for history and analytics."""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user_id
from app.models.verification import Verification

router = APIRouter(tags=["Verification"])


class OutcomeUpdate(BaseModel):
    outcome: str  # completed, cancelled, timeout, error
    cancel_reason: Optional[str] = None
    error_message: Optional[str] = None


@router.patch("/verify/{verification_id}/outcome")
async def record_outcome(
    verification_id: str,
    body: OutcomeUpdate,
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    v = (
        db.query(Verification)
        .filter(
            Verification.id == verification_id,
            Verification.user_id == user_id,
        )
        .first()
    )

    if not v:
        raise HTTPException(status_code=404, detail="Verification not found")

    v.outcome = body.outcome
    if body.cancel_reason:
        v.cancel_reason = body.cancel_reason
    if body.error_message:
        v.error_message = body.error_message

    db.commit()
    return {"success": True}
