"""Admin actions endpoints."""

import logging
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user_id
from app.models.transaction import PaymentLog, Transaction
from app.models.user import User
from app.services.balance_service import BalanceService

logger = logging.getLogger(__name__)
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
        logger.error(f"Failed to trigger maintenance: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to trigger maintenance")


@router.get("/settlements/pending")
async def get_pending_settlements(
    admin_id: str = Depends(require_admin), db: Session = Depends(get_db)
):
    """View all pending crypto settlement intents awaiting audit."""
    try:
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
                    i.processing_started_at.isoformat()
                    if i.processing_started_at
                    else None
                ),
            }
            for i in intents
        ]
    except Exception as e:
        logger.error(f"Error fetching pending settlements: {e}", exc_info=True)
        raise HTTPException(
            status_code=500, detail="Failed to fetch pending settlements"
        )


@router.post("/settlements/cancel/{reference}")
async def cancel_settlement(
    reference: str,
    admin_id: str = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Cancel/dismiss a pending settlement intent (e.g. test artifacts, fraud)."""
    try:
        intent = db.query(PaymentLog).filter(PaymentLog.reference == reference).first()
        if not intent:
            raise HTTPException(status_code=404, detail="Settlement record not found")

        if intent.state == "completed":
            return {
                "status": "error",
                "message": "Cannot cancel a completed settlement",
            }

        intent.state = "cancelled"
        intent.error_message = (
            f"{intent.error_message or ''} | Cancelled by admin {admin_id}"
        ).strip(" |")

        tx = db.query(Transaction).filter(Transaction.reference == reference).first()
        if tx:
            tx.status = "cancelled"

        db.commit()
        return {"status": "success", "message": f"Settlement {reference} cancelled"}
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error cancelling settlement {reference}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to cancel settlement")


@router.post("/settlements/approve/{reference}")
async def approve_settlement(
    reference: str,
    admin_id: str = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Approve and credit a crypto settlement intent."""
    try:
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
            tx = (
                db.query(Transaction).filter(Transaction.reference == reference).first()
            )
            if tx:
                tx.status = "completed"

            db.commit()

            # Wire crypto revenue into recognition table so dashboard totals include it
            try:
                from app.services.revenue_recognition_service import (
                    RevenueRecognitionService,
                )

                if tx:
                    await RevenueRecognitionService(db).recognize_revenue(
                        transaction_id=tx.id,
                        gross_amount=float(intent.amount_usd),
                        provider_cost=0.0,
                        tax_jurisdiction="US",
                    )
            except Exception as rev_err:
                logger.warning(
                    f"Revenue recognition failed for {reference} (non-critical): {rev_err}"
                )

            return {
                "status": "success",
                "message": f"Settled ${intent.amount_usd} to {user.email}",
            }

        raise HTTPException(status_code=500, detail="Failed to apply credits")
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error approving settlement {reference}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to approve settlement")
