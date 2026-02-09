"""Admin stats endpoints."""

from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.dependencies import get_current_user_id
from app.models.user import User

router = APIRouter()


async def require_admin(user_id: str = Depends(get_current_user_id), db: Session = Depends(get_db)):
    """Verify admin access."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user or not user.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")
    return user_id


@router.get("/stats/summary")
async def get_stats_summary(
    admin_id: str = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Get platform stats summary."""
    try:
        from app.models.verification import Verification
        from app.models.transaction import Transaction
        
        # Get counts
        total_users = db.query(User).count()
        total_verifications = db.query(Verification).count()
        total_transactions = db.query(Transaction).count()
        
        # Calculate revenue (sum of credit transactions)
        from sqlalchemy import func
        revenue = db.query(func.sum(Transaction.amount)).filter(
            Transaction.type == 'credit'
        ).scalar() or 0.0
        
        return {
            "summary": {
                "users": total_users,
                "verifications": total_verifications,
                "transactions": total_transactions,
                "revenue": float(revenue)
            },
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    except Exception as e:
        # Fallback if tables don't exist
        return {
            "summary": {
                "users": 0,
                "verifications": 0,
                "transactions": 0,
                "revenue": 0.0
            },
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "error": str(e)
        }


@router.get("/stats")
async def get_stats(
    admin_id: str = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Alias for stats summary."""
    return await get_stats_summary(admin_id, db)
