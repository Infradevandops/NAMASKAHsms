"""Admin Operational Intelligence endpoints."""

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user_id
from app.models.user import User
from app.services.operational_intelligence_service import OperationalIntelligenceService

router = APIRouter()


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
