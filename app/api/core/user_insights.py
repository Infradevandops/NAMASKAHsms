"""User-facing insights endpoints for carrier_analytics and purchase_outcomes."""

from typing import Any, Dict

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import Boolean, func
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user_id
from app.core.logging import get_logger
from app.models.carrier_analytics import CarrierAnalytics
from app.models.notification_analytics import NotificationAnalytics
from app.models.purchase_outcome import PurchaseOutcome
from app.models.refund import Refund
from app.models.user import User

logger = get_logger(__name__)
router = APIRouter(prefix="/api/analytics", tags=["User Insights"])


@router.get("/carrier-insights")
async def get_carrier_insights(
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """Carrier match rates and top carriers for the current user."""
    records = (
        db.query(CarrierAnalytics)
        .filter(CarrierAnalytics.user_id == user_id)
        .all()
    )

    if not records:
        return {"total": 0, "exact_match_rate": 0, "top_carriers": [], "outcomes": {}}

    total = len(records)
    exact_matches = sum(1 for r in records if r.exact_match)

    # Top assigned carriers
    carrier_counts: Dict[str, Dict] = {}
    for r in records:
        c = r.textverified_response or "Unknown"
        if c not in carrier_counts:
            carrier_counts[c] = {"count": 0, "matched": 0}
        carrier_counts[c]["count"] += 1
        if r.exact_match:
            carrier_counts[c]["matched"] += 1

    top_carriers = [
        {
            "carrier": k,
            "count": v["count"],
            "match_rate": round(v["matched"] / v["count"] * 100, 1) if v["count"] else 0,
        }
        for k, v in sorted(carrier_counts.items(), key=lambda x: -x[1]["count"])[:10]
    ]

    # Outcome breakdown
    outcome_counts: Dict[str, int] = {}
    for r in records:
        o = r.outcome or "unknown"
        outcome_counts[o] = outcome_counts.get(o, 0) + 1

    return {
        "total": total,
        "exact_match_rate": round(exact_matches / total * 100, 1) if total else 0,
        "top_carriers": top_carriers,
        "outcomes": outcome_counts,
    }


@router.get("/outcome-insights")
async def get_outcome_insights(
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """Purchase outcome telemetry — latency, categories, refund recoup."""
    records = (
        db.query(PurchaseOutcome)
        .filter(PurchaseOutcome.user_id == user_id)
        .all()
    )

    if not records:
        return {
            "total": 0,
            "avg_latency": None,
            "outcome_categories": {},
            "refund_recoup_rate": 0,
            "top_states": [],
        }

    total = len(records)

    # Average delivery latency
    latencies = [r.latency_seconds for r in records if r.latency_seconds and r.latency_seconds > 0]
    avg_latency = round(sum(latencies) / len(latencies), 1) if latencies else None

    # Outcome category breakdown
    categories: Dict[str, int] = {}
    for r in records:
        cat = r.outcome_category or "UNKNOWN"
        categories[cat] = categories.get(cat, 0) + 1

    # Refund recoup rate
    refunded = [r for r in records if r.is_refunded]
    recouped = sum(1 for r in refunded if r.provider_refunded)
    recoup_rate = round(recouped / len(refunded) * 100, 1) if refunded else 0

    # Top states
    state_counts: Dict[str, int] = {}
    for r in records:
        s = r.assigned_state or "N/A"
        state_counts[s] = state_counts.get(s, 0) + 1

    top_states = [
        {"state": k, "count": v}
        for k, v in sorted(state_counts.items(), key=lambda x: -x[1])[:10]
    ]

    return {
        "total": total,
        "avg_latency": avg_latency,
        "outcome_categories": categories,
        "refund_recoup_rate": recoup_rate,
        "top_states": top_states,
    }


@router.get("/notification-insights")
async def get_notification_insights(
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """Notification delivery and engagement metrics."""
    records = (
        db.query(NotificationAnalytics)
        .filter(NotificationAnalytics.user_id == user_id)
        .all()
    )

    if not records:
        return {"total": 0, "delivery_rate": 0, "avg_delivery_ms": None, "avg_read_ms": None, "by_status": {}, "by_method": {}}

    total = len(records)
    delivered = sum(1 for r in records if r.status in ("delivered", "read", "clicked"))
    delivery_times = [r.delivery_time_ms for r in records if r.delivery_time_ms and r.delivery_time_ms > 0]
    read_times = [r.read_time_ms for r in records if r.read_time_ms and r.read_time_ms > 0]

    by_status: Dict[str, int] = {}
    by_method: Dict[str, int] = {}
    for r in records:
        by_status[r.status or "unknown"] = by_status.get(r.status or "unknown", 0) + 1
        by_method[r.delivery_method or "unknown"] = by_method.get(r.delivery_method or "unknown", 0) + 1

    return {
        "total": total,
        "delivery_rate": round(delivered / total * 100, 1) if total else 0,
        "avg_delivery_ms": round(sum(delivery_times) / len(delivery_times)) if delivery_times else None,
        "avg_read_ms": round(sum(read_times) / len(read_times)) if read_times else None,
        "by_status": by_status,
        "by_method": by_method,
    }


@router.get("/refund-insights")
async def get_refund_insights(
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """Refund timeline and status breakdown."""
    records = (
        db.query(Refund)
        .filter(Refund.user_id == user_id)
        .order_by(Refund.created_at.desc())
        .limit(50)
        .all()
    )

    if not records:
        return {"total": 0, "total_amount": 0, "by_status": {}, "recent": [], "stuck": []}

    total = len(records)
    total_amount = sum(r.amount for r in records if r.amount)

    by_status: Dict[str, int] = {}
    for r in records:
        by_status[r.status or "unknown"] = by_status.get(r.status or "unknown", 0) + 1

    recent = [
        {
            "id": r.id,
            "amount": r.amount,
            "reason": r.reason,
            "status": r.status,
            "initiated_at": r.initiated_at.isoformat() if r.initiated_at else None,
            "processed_at": r.processed_at.isoformat() if r.processed_at else None,
        }
        for r in records[:10]
    ]

    stuck = [
        {
            "id": r.id,
            "amount": r.amount,
            "status": r.status,
            "failed_attempts": r.failed_attempts,
            "next_retry_at": r.next_retry_at.isoformat() if r.next_retry_at else None,
        }
        for r in records
        if r.status == "failed" and r.next_retry_at
    ]

    return {
        "total": total,
        "total_amount": round(total_amount, 2),
        "by_status": by_status,
        "recent": recent,
        "stuck": stuck,
    }
