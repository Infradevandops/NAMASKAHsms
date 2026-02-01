"""Real-time refund monitoring endpoint for admin."""


from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Depends, Query
from sqlalchemy import desc, func
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.dependencies import get_current_admin_user
from app.models.transaction import Transaction
from app.models.user import User
from app.models.verification import Verification
from app.services.auto_refund_service import AutoRefundService

router = APIRouter(prefix="/admin/refunds", tags=["Admin - Refunds"])


@router.get("/monitor")
async def monitor_refunds(
    minutes: int = Query(60, ge=1, le=1440),
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db),
):
    """Real-time refund monitoring dashboard."""
    cutoff = datetime.now(timezone.utc) - timedelta(minutes=minutes)

    # Get all refund transactions
    refunds = (
        db.query(Transaction)
        .filter(
            Transaction.type == "verification_refund",
            Transaction.created_at >= cutoff,
        )
        .order_by(desc(Transaction.created_at))
        .all()
    )

    # Get failed/cancelled verifications without refunds
    failed_verifications = (
        db.query(Verification)
        .filter(
            Verification.status.in_(["timeout", "cancelled", "failed"]),
            Verification.created_at >= cutoff,
        )
        .all()
    )

    # Check which ones don't have refunds
    missing_refunds = []
for v in failed_verifications:
        has_refund = any(r.user_id == v.user_id and v.id in r.description for r in refunds)
if not has_refund:
            missing_refunds.append(
                {
                    "verification_id": v.id,
                    "user_id": v.user_id,
                    "service": v.service_name,
                    "cost": v.cost,
                    "status": v.status,
                    "created_at": v.created_at.isoformat(),
                    "age_minutes": (datetime.now(timezone.utc) - v.created_at).total_seconds() / 60,
                }
            )

    # Calculate stats
    total_refunded = sum(r.amount for r in refunds)
    total_missing = sum(v["cost"] for v in missing_refunds)

    return {
        "period_minutes": minutes,
        "summary": {
            "total_refunds": len(refunds),
            "total_refunded_amount": total_refunded,
            "missing_refunds": len(missing_refunds),
            "missing_refund_amount": total_missing,
            "refund_rate": (
                len(refunds) / (len(refunds) + len(missing_refunds)) * 100
if (len(refunds) + len(missing_refunds)) > 0
                else 100
            ),
        },
        "recent_refunds": [
            {
                "id": r.id,
                "user_id": r.user_id,
                "amount": r.amount,
                "description": r.description,
                "created_at": r.created_at.isoformat(),
            }
for r in refunds[:20]
        ],
        "missing_refunds": missing_refunds[:20],
        "alerts": (
            [
                {
                    "level": "critical",
                    "message": f"{len(missing_refunds)} verifications need refunds (${total_missing:.2f})",
                }
            ]
if len(missing_refunds) > 0
            else []
        ),
    }


@router.post("/process-missing")
async def process_missing_refunds(
    minutes: int = Query(60, ge=1, le=1440),
    dry_run: bool = Query(True),
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db),
):
    """Process all missing refunds."""

    refund_service = AutoRefundService(db)
    result = refund_service.reconcile_unrefunded_verifications(days_back=minutes // 1440 or 1, dry_run=dry_run)

    return {
        "dry_run": dry_run,
        "result": result,
        "message": (
            f"Would refund {result['needs_refund']} verifications (${result['total_amount_refunded']:.2f})"
if dry_run
            else f"Refunded {result['refunded_now']} verifications (${result['total_amount_refunded']:.2f})"
        ),
    }


@router.get("/stats")
async def refund_stats(
    days: int = Query(7, ge=1, le=90),
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db),
):
    """Refund statistics over time."""
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)

    # Daily refund stats
    daily_stats = (
        db.query(
            func.date(Transaction.created_at).label("date"),
            func.count(Transaction.id).label("count"),
            func.sum(Transaction.amount).label("total"),
        )
        .filter(Transaction.type == "verification_refund", Transaction.created_at >= cutoff)
        .group_by(func.date(Transaction.created_at))
        .order_by(desc(func.date(Transaction.created_at)))
        .all()
    )

    # Verification failure stats
    failure_stats = (
        db.query(Verification.status, func.count(Verification.id).label("count"))
        .filter(
            Verification.status.in_(["timeout", "cancelled", "failed"]),
            Verification.created_at >= cutoff,
        )
        .group_by(Verification.status)
        .all()
    )

    return {
        "period_days": days,
        "daily_refunds": [{"date": str(d.date), "count": d.count, "total": float(d.total)} for d in daily_stats],
        "failure_breakdown": [{"status": f.status, "count": f.count} for f in failure_stats],
        "total_refunds": sum(d.count for d in daily_stats),
        "total_amount": sum(d.total for d in daily_stats),
    }
