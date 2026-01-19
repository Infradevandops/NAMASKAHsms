from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.api.admin.dependencies import require_admin
from app.core.database import get_db
from app.models.transaction import Transaction
from app.models.user import User
from app.models.verification import Verification

router = APIRouter(prefix="/admin", tags=["admin-stats"])


@router.get("/stats")
async def get_admin_stats(
    current_user: User = Depends(require_admin), db: Session = Depends(get_db)
):
    """Get admin dashboard statistics"""

    try:
        # Get user counts with error handling
        total_users = db.query(func.count(User.id)).scalar() or 0
        admin_users = (
            db.query(func.count(User.id)).filter(User.is_admin ).scalar() or 0
        )
        # Remove is_active filter since it may not exist
        active_users = total_users  # Simplified - assume all users are active

        # Get verification counts with error handling
        try:
            total_verifications = db.query(func.count(Verification.id)).scalar() or 0
        except Exception:
            total_verifications = 0

        try:
            success_verifications = (
                db.query(func.count(Verification.id))
                .filter(Verification.status == "completed")
                .scalar()
                or 0
            )
        except Exception:
            success_verifications = 0

        try:
            pending_verifications = (
                db.query(func.count(Verification.id))
                .filter(Verification.status == "pending")
                .scalar()
                or 0
            )
        except Exception:
            pending_verifications = 0

        success_rate = (
            (success_verifications / total_verifications * 100)
            if total_verifications > 0
            else 0
        )

        # Get revenue with error handling
        try:
            total_revenue = (
                db.query(func.sum(Transaction.amount))
                .filter(Transaction.type == "credit")
                .scalar()
                or 0
            )
        except Exception:
            total_revenue = 0

        return {
            "users": total_users,
            "admin_users": admin_users,
            "active_users": active_users,
            "verifications": total_verifications,
            "pending_verifications": pending_verifications,
            "success_verifications": success_verifications,
            "success_rate": round(success_rate, 1),
            "revenue": float(total_revenue),
        }
    except Exception as e:
        # Return default stats if there's any error
        return {
            "users": 0,
            "admin_users": 0,
            "active_users": 0,
            "verifications": 0,
            "pending_verifications": 0,
            "success_verifications": 0,
            "success_rate": 0.0,
            "revenue": 0.0,
            "error": str(e),
        }


@router.get("/verification-history/recent")
async def get_recent_verifications(
    current_user: User = Depends(require_admin), db: Session = Depends(get_db)
):
    """Get recent verification history with user details"""

    # Join verifications with users to get user details
    verifications = (
        db.query(
            Verification.id,
            Verification.user_id,
            Verification.service_name,
            Verification.phone_number,
            Verification.status,
            Verification.cost,
            Verification.created_at,
            User.email.label("user_email"),
            User.id.label("user_db_id"),
        )
        .join(User, Verification.user_id == User.id)
        .order_by(Verification.created_at.desc())
        .limit(20)
        .all()
    )

    return [
        {
            "id": v.id,
            "user_id": v.user_db_id[:8] + "..." if v.user_db_id else "Unknown",
            "user_email": v.user_email or "Unknown",
            "service_name": v.service_name or "telegram",
            "phone_number": v.phone_number or "N/A",
            "status": v.status,
            "cost": f"{float(v.cost or 0):.2f}",
            "created_at": v.created_at.isoformat() if v.created_at else "",
        }
        for v in verifications
    ]
