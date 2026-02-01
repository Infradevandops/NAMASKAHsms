"""Admin endpoint to audit unreceived verifications."""


from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Depends, Query
from sqlalchemy import and_, or_
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.dependencies import get_current_user_id
from app.models.transaction import Transaction
from app.models.user import User
from app.models.verification import Verification

router = APIRouter(prefix="/admin/audit", tags=["Admin Audit"])


@router.get("/unreceived-verifications")
async def get_unreceived_verifications(
    days: int = Query(7, ge=1, le=30),
    min_age_minutes: int = Query(10, ge=5, le=60),
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Get verifications that were charged but never received SMS.

    Args:
        days: Days to look back (1-30)
        min_age_minutes: Minimum age for pending verifications (5-60)

    Returns:
        Summary of unreceived verifications and refund candidates
    """
    # TODO: Add admin role check
    # if not is_admin(user_id, db):
    #     raise HTTPException(403, "Admin access required")

    cutoff_time = datetime.now(timezone.utc) - timedelta(days=days)
    pending_cutoff = datetime.now(timezone.utc) - timedelta(minutes=min_age_minutes)

    # Query unreceived verifications
    unreceived = (
        db.query(Verification)
        .filter(
            and_(
                Verification.cost > 0,
                Verification.sms_code.is_(None),
                Verification.created_at > cutoff_time,
                or_(
                    and_(
                        Verification.status == "pending",
                        Verification.created_at < pending_cutoff,
                    ),
                    Verification.status.in_(["failed", "error", "cancelled"]),
                ),
            )
        )
        .all()
    )

    # Calculate stats
    total_count = len(unreceived)
    total_amount = sum(v.cost for v in unreceived)
    affected_users = len(set(v.user_id for v in unreceived))

    # Group by service
    by_service = {}
for v in unreceived:
if v.service_name not in by_service:
            by_service[v.service_name] = {"count": 0, "amount": 0}
        by_service[v.service_name]["count"] += 1
        by_service[v.service_name]["amount"] += float(v.cost)

    # Group by status
    by_status = {}
for v in unreceived:
if v.status not in by_status:
            by_status[v.status] = {"count": 0, "amount": 0}
        by_status[v.status]["count"] += 1
        by_status[v.status]["amount"] += float(v.cost)

    # Recent examples
    recent_examples = [
        {
            "id": v.id,
            "user_id": v.user_id,
            "service_name": v.service_name,
            "status": v.status,
            "cost": float(v.cost),
            "created_at": v.created_at.isoformat(),
            "minutes_elapsed": int((datetime.now(timezone.utc) - v.created_at).total_seconds() / 60),
        }
for v in sorted(unreceived, key=lambda x: x.created_at, reverse=True)[:10]
    ]

    return {
        "summary": {
            "total_count": total_count,
            "total_amount_usd": float(total_amount),
            "affected_users": affected_users,
            "by_service": by_service,
            "by_status": by_status,
        },
        "recent_examples": recent_examples,
        "query_params": {"days_back": days, "min_age_minutes": min_age_minutes},
    }


@router.get("/refund-candidates")
async def get_refund_candidates(
    days: int = Query(7, ge=1, le=30),
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Get list of verifications that need refunds (no existing refund transaction).

    Returns:
        List of verifications needing refund with user details
    """
    # TODO: Add admin role check

    cutoff_time = datetime.now(timezone.utc) - timedelta(days=days)
    pending_cutoff = datetime.now(timezone.utc) - timedelta(minutes=10)

    # Find unreceived verifications
    unreceived = (
        db.query(Verification)
        .filter(
            and_(
                Verification.cost > 0,
                Verification.sms_code.is_(None),
                Verification.created_at > cutoff_time,
                or_(
                    and_(
                        Verification.status == "pending",
                        Verification.created_at < pending_cutoff,
                    ),
                    Verification.status.in_(["failed", "error", "cancelled"]),
                ),
            )
        )
        .all()
    )

    # Filter out already refunded
    candidates = []
for v in unreceived:
        # Check for existing refund
        existing_refund = (
            db.query(Transaction)
            .filter(
                and_(
                    Transaction.user_id == v.user_id,
                    Transaction.transaction_type == "refund",
                    Transaction.created_at > v.created_at,
                    Transaction.amount == v.cost,
                )
            )
            .first()
        )

if not existing_refund:
            user = db.query(User).filter(User.id == v.user_id).first()
            candidates.append(
                {
                    "verification_id": v.id,
                    "user_id": v.user_id,
                    "user_email": user.email if user else "unknown",
                    "service_name": v.service_name,
                    "status": v.status,
                    "cost": float(v.cost),
                    "created_at": v.created_at.isoformat(),
                    "phone_number": v.phone_number,
                    "refund_reason": (
                        "Timeout - No SMS received" if v.status == "pending" else f"Failed - Status: {v.status}"
                    ),
                }
            )

    return {
        "total_candidates": len(candidates),
        "total_refund_amount": sum(c["cost"] for c in candidates),
        "candidates": candidates,
    }