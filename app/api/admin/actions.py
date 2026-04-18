"""Admin actions endpoints."""

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user_id
from app.models.transaction import PaymentLog, Transaction
from app.models.user import User
from app.services.balance_service import BalanceService

router = APIRouter()


async def require_admin(
    user_id: str = Depends(get_current_user_id), db: Session = Depends(get_db)
):
    """Verify admin access."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user or not user.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")
    return user_id


@router.post("/actions/system-maintenance")
async def trigger_system_maintenance(
    admin_id: str = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Trigger system maintenance."""
    try:
        return {
            "action": "system_maintenance",
            "status": "initiated",
            "admin_id": admin_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to trigger maintenance: {str(e)}"
        )


@router.get("/settlements/pending")
async def get_pending_settlements(
    admin_id: str = Depends(require_admin), db: Session = Depends(get_db)
):
    """View all pending crypto settlement intents awaiting audit."""
    intents = (
        db.query(PaymentLog)
        .filter(PaymentLog.state.in_(["pending", "processing"]))
        .all()
    )

    return [
        {
            "id": i.id,
            "user_id": i.user_id,
            "email": i.email,
            "amount_usd": float(i.amount_usd),
            "method": i.payment_method,
            "reference": i.reference,
            "telemetry": i.error_message,
            "created_at": (
                i.processing_started_at.isoformat() if i.processing_started_at else None
            ),
        }
        for i in intents
    ]


@router.post("/settlements/approve/{reference}")
async def approve_settlement(
    reference: str,
    admin_id: str = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Approve and credit a crypto settlement intent."""
    intent = db.query(PaymentLog).filter(PaymentLog.reference == reference).first()
    if not intent:
        raise HTTPException(status_code=404, detail="Settlement record not found")

    if intent.state == "completed":
        return {"status": "error", "message": "Settlement already processed"}

    # Standardize the intent record
    user = db.query(User).filter(User.id == intent.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Atomic Balance Sync
    balance_service = BalanceService(db)
    success = balance_service.sync_credits_with_admin(
        user_id=intent.user_id,
        new_balance=float(user.credits or 0) + float(intent.amount_usd),
        reason=f"Settlement Approved: {reference}",
    )

    if success:
        intent.state = "completed"
        intent.processed_at = datetime.now(timezone.utc)

        # Mark associated transaction as completed
        tx = db.query(Transaction).filter(Transaction.reference == reference).first()
        if tx:
            tx.status = "completed"

        db.commit()
        return {
            "status": "success",
            "message": f"Settled ${intent.amount_usd} to {user.email}",
        }

    raise HTTPException(status_code=500, detail="Failed to apply credits")
