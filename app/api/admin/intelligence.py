"""Admin Operational Intelligence endpoints."""

from typing import Any, Dict, List, Optional  # noqa: F401

from fastapi import APIRouter, Body, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user_id
from app.models.user import User
from app.services.operational_intelligence_service import (  # noqa: E501
    OperationalIntelligenceService,
)

router = APIRouter()


class TargetSetRequest(BaseModel):
    target_count: int
    revenue_target: float = 4000.00
    notes: str = ""


async def require_admin(
    user_id: str = Depends(get_current_user_id), db: Session = Depends(get_db)
):
    """Verify admin access."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user or not user.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")
    return user_id


@router.get("/intelligence/vitality")
async def get_user_vitality(
    days: int = Query(30),
    admin_id: str = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Get DAU, Signup Velocity, and Power User data."""
    service = OperationalIntelligenceService(db)
    return await service.get_user_vitality(days=days)


@router.get("/intelligence/audit/margin")
async def get_margin_audit(
    limit: int = Query(50),
    admin_id: str = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Detect platform price leakage (Margin Drift)."""
    service = OperationalIntelligenceService(db)
    return await service.get_margin_audit(limit=limit)


@router.get("/intelligence/load-heatmap")
async def get_load_heatmap(
    admin_id: str = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Get hourly verification attempt distribution."""
    service = OperationalIntelligenceService(db)
    return await service.get_system_load_heatmap()


@router.get("/intelligence/audit/trail")
async def get_audit_trail(
    limit: int = Query(20),
    admin_id: str = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Get history of pricing and configuration changes."""
    service = OperationalIntelligenceService(db)
    return await service.get_audit_trail(limit=limit)


@router.get("/intelligence/cohorts")
async def get_cohort_retention(
    admin_id: str = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Get 90-day weekly cohort retention data."""
    from app.services.cohort_service import CohortRetentionService

    service = CohortRetentionService(db)
    return await service.get_90d_retention_data()


@router.get("/intelligence/forensics/history")
async def get_forensic_history(
    limit: int = Query(50),
    offset: int = Query(0),
    admin_id: str = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Get verification history with row-level profit forensics."""
    service = OperationalIntelligenceService(db)
    return await service.get_forensic_history(limit=limit, offset=offset)


@router.get("/intelligence/targets")
async def get_growth_targets(
    admin_id: str = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Get persistent growth targets and projections."""
    from app.services.target_tracking_service import TargetTrackingService

    service = TargetTrackingService(db)
    return await service.get_growth_projections()


@router.get("/intelligence/revenue/recognition")
async def get_revenue_recognition(
    period: str = Query(
        None, description="YYYY-MM, defaults to current month"
    ),  # noqa: E501
    admin_id: str = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Get recognized vs deferred revenue summary for a period."""
    from datetime import datetime, timezone

    from app.services.revenue_recognition_service import (  # noqa: E501
        RevenueRecognitionService,
    )

    if not period:
        period = datetime.now(timezone.utc).strftime("%Y-%m")
    service = RevenueRecognitionService(db)
    recognized = await service.get_revenue_by_period(period)
    deferred = await service.get_deferred_revenue_summary()
    return {"period": period, "recognized": recognized, "deferred": deferred}


@router.get("/intelligence/disputes")
async def get_open_disputes(
    admin_id: str = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Get all open payment disputes."""
    from app.services.dispute_service import DisputeService

    service = DisputeService(db)
    return await service.get_open_disputes()


@router.post("/intelligence/disputes/{dispute_id}/resolve")
async def resolve_dispute(
    dispute_id: str,
    resolution: str = Body(...),
    notes: str = Body(""),
    admin_id: str = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Resolve a dispute (won/lost/appealed)."""
    from app.services.dispute_service import DisputeService

    service = DisputeService(db)
    try:
        return await service.process_chargeback(dispute_id, resolution, notes)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/intelligence/commissions/pending")
async def get_pending_commissions(
    admin_id: str = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Get pending commission payouts for affiliates."""
    from app.models.commission import RevenueShare

    shares = (
        db.query(RevenueShare)
        .filter(RevenueShare.status == "pending")
        .order_by(RevenueShare.created_at.desc())
        .limit(100)
        .all()
    )
    total = sum(float(s.commission_amount) for s in shares)
    return {
        "pending_count": len(shares),
        "total_pending": round(total, 2),
        "items": [
            {
                "id": s.id,
                "partner_id": s.partner_id,
                "commission_amount": float(s.commission_amount),
                "tier_name": s.tier_name,
                "created_at": s.created_at,
            }
            for s in shares
        ],
    }


@router.get("/intelligence/revenue")
async def get_revenue_metrics(
    days: int = Query(30),
    admin_id: str = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Get real revenue metrics from transactions."""
    from datetime import datetime, timedelta, timezone

    from sqlalchemy import func

    from app.models.transaction import Transaction

    start = datetime.now(timezone.utc) - timedelta(days=days)
    row = (
        db.query(
            func.coalesce(func.sum(Transaction.amount), 0).label("total"),
            func.count(Transaction.id).label("count"),
        )
        .filter(
            Transaction.status == "success", Transaction.created_at >= start
        )  # noqa: E501
        .first()
    )
    return {
        "period_days": days,
        "total_revenue": float(row.total),
        "transaction_count": row.count,
    }


@router.get("/intelligence/fraud/metrics")
async def get_fraud_metrics(
    admin_id: str = Depends(require_admin),
):
    """Get fraud detection model metrics."""
    from app.services.fraud_detection_service import FraudDetectionService

    service = FraudDetectionService()
    return await service.get_model_metrics()


@router.get("/intelligence/refunds/failed")
async def get_failed_refunds(
    admin_id: str = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Get failed refunds pending retry."""
    from app.services.failed_refund_service import FailedRefundService

    service = FailedRefundService(db)
    return await service.get_failed_refunds_pending_retry()


@router.post("/intelligence/targets/set")
async def set_growth_target(
    payload: TargetSetRequest,
    admin_id: str = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Update the active monthly growth target."""
    from decimal import Decimal

    from app.services.target_tracking_service import TargetTrackingService

    service = TargetTrackingService(db)
    target = await service.get_active_target()
    target.target_count = payload.target_count
    target.revenue_target = Decimal(str(payload.revenue_target))
    if payload.notes:
        target.notes = payload.notes
    db.commit()
    db.refresh(target)
    return {
        "month": target.month,
        "target_count": target.target_count,
        "revenue_target": float(target.revenue_target),
    }


@router.get("/intelligence/compliance/report")
async def get_compliance_report(
    admin_id: str = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Generate institutional SOC 2 compliance report."""
    from app.services.compliance_service import ComplianceService

    service = ComplianceService(db)
    return await service.generate_audit_report()


@router.get("/intelligence/audit/logs")
async def get_audit_logs(
    limit: int = Query(50),
    offset: int = Query(0),
    admin_id: str = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Fetch persistent system audit logs."""
    from app.services.audit_service import AuditService

    service = AuditService(db)
    return await service.get_system_audit_logs(limit=limit, offset=offset)
