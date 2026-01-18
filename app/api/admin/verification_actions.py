from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.user import User
from app.models.verification import Verification
from app.api.admin.dependencies import require_admin
from datetime import datetime

router = APIRouter(prefix="/admin/verifications", tags=["admin-verifications"])


@router.post("/{verification_id}/cancel")
async def cancel_verification(
    verification_id: str, admin_user: User = Depends(require_admin), db: Session = Depends(get_db)
):
    """Cancel a pending verification"""

    verification = db.query(Verification).filter(Verification.id == verification_id).first()
    if not verification:
        raise HTTPException(status_code=404, detail="Verification not found")

    if verification.status != "pending":
        raise HTTPException(status_code=400, detail="Can only cancel pending verifications")

    # Update verification status
    verification.status = "cancelled"
    verification.completed_at = datetime.utcnow()

    # Refund credits to user if applicable
    if verification.cost and verification.cost > 0:
        from app.models.user import User

        user = db.query(User).filter(User.id == verification.user_id).first()
        if user:
            user.credits = (user.credits or 0) + verification.cost

    db.commit()

    return {
        "success": True,
        "message": f"Verification {verification_id} cancelled and credits refunded",
    }


@router.get("/{verification_id}")
async def get_verification_details(
    verification_id: str, admin_user: User = Depends(require_admin), db: Session = Depends(get_db)
):
    """Get detailed verification information"""

    verification = db.query(Verification).filter(Verification.id == verification_id).first()
    if not verification:
        raise HTTPException(status_code=404, detail="Verification not found")

    user = db.query(User).filter(User.id == verification.user_id).first()

    return {
        "success": True,
        "verification": {
            "verification_id": verification.id,
            "user_id": verification.user_id,
            "user_email": user.email if user else "Unknown",
            "service_name": verification.service_name,
            "phone_number": verification.phone_number,
            "country": verification.country,
            "status": verification.status,
            "cost": float(verification.cost or 0),
            "provider": verification.provider,
            "activation_id": verification.activation_id,
            "sms_code": verification.sms_code,
            "sms_text": verification.sms_text,
            "created_at": verification.created_at.isoformat() if verification.created_at else None,
            "completed_at": (
                verification.completed_at.isoformat() if verification.completed_at else None
            ),
            "sms_received_at": (
                verification.sms_received_at.isoformat() if verification.sms_received_at else None
            ),
        },
    }


@router.post("/bulk-cancel")
async def bulk_cancel_verifications(
    verification_ids: list[str],
    admin_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Cancel multiple verifications at once"""

    cancelled_count = 0
    refunded_amount = 0.0

    for verification_id in verification_ids:
        verification = db.query(Verification).filter(Verification.id == verification_id).first()
        if verification and verification.status == "pending":
            verification.status = "cancelled"
            verification.completed_at = datetime.utcnow()

            # Refund credits
            if verification.cost and verification.cost > 0:
                user = db.query(User).filter(User.id == verification.user_id).first()
                if user:
                    user.credits = (user.credits or 0) + verification.cost
                    refunded_amount += verification.cost

            cancelled_count += 1

    db.commit()

    return {
        "success": True,
        "cancelled_count": cancelled_count,
        "refunded_amount": refunded_amount,
        "message": f"Cancelled {cancelled_count} verifications, refunded ${refunded_amount:.2f}",
    }
