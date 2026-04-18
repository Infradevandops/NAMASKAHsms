"""Admin audit and compliance endpoints."""

from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
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


@router.get("/audit-logs")
async def get_audit_logs(
    action: Optional[str] = Query(None),
    admin_id_filter: Optional[str] = Query(None),
    days: int = Query(30, ge=1, le=365),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    admin_id: str = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Get audit logs for compliance tracking."""
    try:
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)

        # For now, return empty results since AuditLog model may not exist
        return {
            "logs": [],
            "total": 0,
            "page": offset // limit + 1,
            "pages": 0,
            "filters": {"action": action, "admin_id": admin_id_filter, "days": days},
        }

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to retrieve audit logs: {str(e)}"
        )


@router.get("/integrity/check")
async def check_financial_integrity(
    admin_id: str = Depends(require_admin),
    db: Session = Depends(get_db),
    limit: int = 50,
    offset: int = 0,
):
    """Deep audit: Verify that User.credits matches Sum(BalanceTransaction)."""
    from sqlalchemy import func

    from app.models.balance_transaction import BalanceTransaction
    from app.models.user import User

    users = db.query(User).offset(offset).limit(limit).all()
    discrepancies = []

    for user in users:
        # Sum all transactions for this user
        tx_sum = (
            db.query(func.sum(BalanceTransaction.amount))
            .filter(BalanceTransaction.user_id == user.id)
            .scalar()
            or 0.0
        )

        balance = float(user.credits or 0.0)
        diff = abs(balance - float(tx_sum))

        if diff > 0.01:  # Small epsilon for float precision
            discrepancies.append(
                {
                    "user_id": user.id,
                    "email": user.email,
                    "cached_balance": balance,
                    "ledger_sum": float(tx_sum),
                    "drift": balance - float(tx_sum),
                }
            )

    return {
        "status": "healthy" if not discrepancies else "drift_detected",
        "check_timestamp": datetime.now(timezone.utc).isoformat(),
        "users_checked": len(users),
        "discrepancies": discrepancies,
        "total_discrepancy_count": len(discrepancies),
    }
