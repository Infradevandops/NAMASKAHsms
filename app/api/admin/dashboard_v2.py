"""Admin dashboard V2 - High-density institutional metrics."""

from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import desc, func
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user_id
from app.models.purchase_outcome import PurchaseOutcome
from app.models.user import User
from app.models.verification import Verification
from app.services.analytics_service import AnalyticsService

router = APIRouter()


async def require_admin(
    user_id: str = Depends(get_current_user_id), db: Session = Depends(get_db)
):
    """Verify admin access."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user or not user.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")
    return user_id


@router.get("/dashboard/v2/stats")
async def get_dashboard_v2_stats(
    admin_id: str = Depends(require_admin), db: Session = Depends(get_db)
):
    """Refined high-density metrics for the premium admin interface."""
    try:
        analytics = AnalyticsService(db)
        overview = await analytics.get_overview()

        # Get refund metrics for the last 30 days
        refund_metrics = await analytics.get_refund_metrics(days=30)

        # Provider Health Data (Phase 12 Real-time)
        provider_stats = (
            db.query(
                PurchaseOutcome.provider,
                func.count(PurchaseOutcome.id).label("total"),
                func.sum(
                    func.case([(PurchaseOutcome.sms_received == True, 1)], else_=0)
                ).label("success"),
                func.avg(PurchaseOutcome.latency_seconds).label("avg_latency"),
            )
            .group_by(PurchaseOutcome.provider)
            .all()
        )

        providers = []
        for row in provider_stats:
            success = row.success or 0
            total = row.total or 1
            providers.append(
                {
                    "name": row.provider or "Unknown",
                    "success_rate": round(success / total * 100, 1),
                    "avg_latency": round(row.avg_latency or 0, 2),
                    "total_volume": total,
                }
            )

        # Recent activities (mocked for now, pending detailed audit logs)
        recent_verifications = (
            db.query(Verification)
            .order_by(Verification.created_at.desc())
            .limit(5)
            .all()
        )
        activities = [
            {
                "type": "verification",
                "user_id": v.user_id,
                "service": v.service_name,
                "status": v.status,
                "time": v.created_at.isoformat() if v.created_at else None,
            }
            for v in recent_verifications
        ]

        return {
            "overview": {
                "total_users": overview["users"]["total"],
                "active_users": overview["users"]["active"],
                "success_rate": overview["verifications"]["rate"],
                "total_revenue": overview["revenue"]["gross"],
            },
            "financial": {
                "gross": refund_metrics["total_revenue"],
                "refunds": refund_metrics["total_refunds"],
                "net": refund_metrics["net_revenue"],
                "refund_rate": refund_metrics["refund_rate"],
            },
            "providers": providers,
            "activities": activities,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
    except Exception as e:
        import logging

        logging.getLogger(__name__).error(f"Dashboard V2 stats failed: {e}")
        raise HTTPException(
            status_code=500, detail="Failed to aggregate institutional stats"
        )


@router.get("/dashboard/v2/rentals", summary="V6.0 Rental Overview")
async def get_rental_overview(
    admin_id: str = Depends(require_admin), db: Session = Depends(get_db)
):
    """Institutional rental overview — all active rentals across all users.

    Returns aggregate stats and a list of active/expiring rentals for the admin panel.
    """
    try:
        from datetime import datetime, timedelta, timezone

        from app.models.verification import NumberRental

        now = datetime.now(timezone.utc)
        warning_threshold = now + timedelta(minutes=30)

        active_rentals = (
            db.query(NumberRental)
            .filter(NumberRental.status == "active")
            .order_by(NumberRental.expires_at.asc())
            .all()
        )

        expiring_soon = []
        healthy = []

        for r in active_rentals:
            expires_at = r.expires_at
            if expires_at.tzinfo is None:
                expires_at = expires_at.replace(tzinfo=timezone.utc)
            remaining_minutes = (expires_at - now).total_seconds() / 60
            entry = {
                "id": r.id,
                "user_id": r.user_id,
                "phone_number": r.phone_number,
                "service": r.service_name,
                "expires_at": r.expires_at.isoformat() if r.expires_at else None,
                "remaining_minutes": round(remaining_minutes, 1),
                "cost": r.cost,
                "warning_sent": r.warning_sent,
            }
            if remaining_minutes <= 30:
                expiring_soon.append(entry)
            else:
                healthy.append(entry)

        return {
            "summary": {
                "total_active": len(active_rentals),
                "expiring_within_30min": len(expiring_soon),
                "healthy": len(healthy),
            },
            "expiring_soon": expiring_soon,
            "healthy_rentals": healthy,
            "timestamp": now.isoformat(),
        }
    except Exception as e:
        import logging

        logging.getLogger(__name__).error(f"Rental overview failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to get rental overview")


@router.get("/dashboard/v2/liquidity-alarms", summary="V6.0 Liquidity Alarms Feed")
async def get_liquidity_alarms(
    limit: int = 20,
    admin_id: str = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Returns the most recent LIQUIDITY_ALARM entries from the ActivityLog.

    These are emitted by the institutional health audit loop when a provider
    balance falls below the $10.00 threshold.
    """
    try:
        from app.models.system import ActivityLog

        alarms = (
            db.query(ActivityLog)
            .filter(ActivityLog.action == "LIQUIDITY_ALARM")
            .order_by(ActivityLog.created_at.desc())
            .limit(limit)
            .all()
        )

        return {
            "alarms": [
                {
                    "id": a.id,
                    "provider": a.element,
                    "status": a.status,
                    "details": a.details,
                    "error_message": a.error_message,
                    "created_at": a.created_at.isoformat() if a.created_at else None,
                }
                for a in alarms
            ],
            "total": len(alarms),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
    except Exception as e:
        import logging

        logging.getLogger(__name__).error(f"Liquidity alarms fetch failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch liquidity alarms")
