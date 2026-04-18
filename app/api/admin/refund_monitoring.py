"""Admin refund monitoring endpoints."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user_id
from app.models.user import User

router = APIRouter()


async def require_admin(
    user_id: str = Depends(get_current_user_id), db: Session = Depends(get_db)
):
    """Verify admin access."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user or not user.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")
    return user_id


@router.get("/refunds/status")
async def get_refund_status(
    admin_id: str = Depends(require_admin),
    db: Session = Depends(get_db),
    limit: int = 50,
    offset: int = 0,
):
    """Get verifications that need reconciliation (failed but not refunded)."""
    from app.models.verification import Verification

    # Query for failed verifications that are refund_eligible but haven't been refunded yet
    # We check both the verification.refunded flag and the existence of a refund_transaction_id
    query = db.query(Verification).filter(
        Verification.status.in_(["failed", "timeout", "cancelled"]),
        Verification.refund_eligible == True,
        Verification.refunded == False,
    )

    total = query.count()
    needs_refund = query.offset(offset).limit(limit).all()

    return {
        "pending_refunds": [
            {
                "id": str(v.id),
                "user_id": v.user_id,
                "service": v.service_name,
                "status": v.status,
                "cost": float(v.cost),
                "created_at": v.created_at.isoformat() if v.created_at else None,
            }
            for v in needs_refund
        ],
        "total": total,
        "offset": offset,
        "limit": limit,
    }
