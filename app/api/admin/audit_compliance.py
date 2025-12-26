"""Admin audit and compliance endpoints."""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from datetime import datetime, timezone, timedelta
from typing import Optional
import json

from app.core.database import get_db
from app.core.dependencies import get_current_user_id
from app.models.user import User
from app.models.audit_log import AuditLog
from app.core.logging import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/admin/compliance", tags=["Admin Audit & Compliance"])


async def require_admin(user_id: str = Depends(get_current_user_id), db: Session = Depends(get_db)):
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
    db: Session = Depends(get_db)
):
    """Get audit logs for compliance tracking."""
    try:
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)
        
        query = db.query(AuditLog).filter(AuditLog.created_at >= cutoff_date)
        
        if action:
            query = query.filter(AuditLog.action == action)
        
        if admin_id_filter:
            query = query.filter(AuditLog.user_id == admin_id_filter)
        
        total = query.count()
        logs = query.order_by(AuditLog.created_at.desc()).limit(limit).offset(offset).all()
        
        return {
            "total": total,
            "limit": limit,
            "offset": offset,
            "period_days": days,
            "logs": [
                {
                    "id": log.id,
                    "admin_id": log.user_id,
                    "action": log.action,
                    "resource_type": log.resource_type,
                    "resource_id": log.resource_id,
                    "details": log.details,
                    "ip_address": log.ip_address,
                    "created_at": log.created_at.isoformat() if log.created_at else None
                }
                for log in logs
            ]
        }
    except Exception as e:
        logger.error(f"Get audit logs error: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch audit logs")


@router.get("/reports")
async def get_compliance_report(
    report_type: str = Query("summary"),
    days: int = Query(30, ge=1, le=365),
    admin_id: str = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Generate compliance report."""
    try:
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)
        
        # Get audit logs
        audit_logs = db.query(AuditLog).filter(
            AuditLog.created_at >= cutoff_date
        ).all()
        
        # Get user changes
        user_changes = [log for log in audit_logs if log.resource_type == "user"]
        
        # Get tier changes
        tier_changes = [log for log in audit_logs if log.action == "tier_update"]
        
        # Get suspension/ban actions
        enforcement_actions = [log for log in audit_logs if log.action in ["suspend", "ban"]]
        
        # Get data access logs
        data_access = [log for log in audit_logs if log.action == "data_export"]
        
        report = {
            "report_type": report_type,
            "period_days": days,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "summary": {
                "total_audit_logs": len(audit_logs),
                "user_changes": len(user_changes),
                "tier_changes": len(tier_changes),
                "enforcement_actions": len(enforcement_actions),
                "data_access_events": len(data_access)
            },
            "actions_by_admin": {},
            "actions_by_type": {}
        }
        
        # Group by admin
        for log in audit_logs:
            admin = log.user_id or "system"
            if admin not in report["actions_by_admin"]:
                report["actions_by_admin"][admin] = 0
            report["actions_by_admin"][admin] += 1
        
        # Group by action type
        for log in audit_logs:
            action = log.action or "unknown"
            if action not in report["actions_by_type"]:
                report["actions_by_type"][action] = 0
            report["actions_by_type"][action] += 1
        
        logger.info(f"Admin {admin_id} generated compliance report")
        
        return report
    except Exception as e:
        logger.error(f"Get compliance report error: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate compliance report")


@router.post("/export")
async def export_user_data(
    user_id: str = Query(...),
    admin_id: str = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Export user data for GDPR compliance (data subject access request)."""
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Get user data
        user_data = {
            "id": user.id,
            "email": user.email,
            "tier": getattr(user, 'tier_id', 'payg') or 'payg',
            "credits": float(user.credits or 0),
            "created_at": user.created_at.isoformat() if user.created_at else None,
            "updated_at": user.updated_at.isoformat() if hasattr(user, 'updated_at') and user.updated_at else None
        }
        
        # Get verifications
        from app.models.verification import Verification
        verifications = db.query(Verification).filter(
            Verification.user_id == user_id
        ).all()
        
        verification_data = [
            {
                "id": v.id,
                "country": v.country,
                "service": v.service_name,
                "status": v.status,
                "created_at": v.created_at.isoformat() if v.created_at else None,
                "completed_at": v.completed_at.isoformat() if v.completed_at else None,
                "cost_usd": float(v.cost or 0)
            }
            for v in verifications
        ]
        
        # Get API keys
        from app.models.api_key import APIKey
        api_keys = db.query(APIKey).filter(APIKey.user_id == user_id).all()
        
        api_key_data = [
            {
                "id": k.id,
                "name": k.name,
                "created_at": k.created_at.isoformat() if k.created_at else None,
                "last_used": k.last_used.isoformat() if hasattr(k, 'last_used') and k.last_used else None
            }
            for k in api_keys
        ]
        
        # Get audit logs related to user
        audit_logs = db.query(AuditLog).filter(
            (AuditLog.resource_id == user_id) | (AuditLog.user_id == user_id)
        ).all()
        
        audit_data = [
            {
                "action": log.action,
                "resource_type": log.resource_type,
                "details": log.details,
                "created_at": log.created_at.isoformat() if log.created_at else None
            }
            for log in audit_logs
        ]
        
        export_data = {
            "export_date": datetime.now(timezone.utc).isoformat(),
            "user": user_data,
            "verifications": verification_data,
            "api_keys": api_key_data,
            "audit_logs": audit_data,
            "summary": {
                "total_verifications": len(verification_data),
                "total_api_keys": len(api_key_data),
                "total_audit_events": len(audit_data)
            }
        }
        
        logger.info(f"Admin {admin_id} exported data for user {user_id} (GDPR request)")
        
        return {
            "success": True,
            "message": f"Data exported for user {user_id}",
            "data": export_data
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Export user data error: {e}")
        raise HTTPException(status_code=500, detail="Failed to export user data")


@router.post("/delete-user-data")
async def delete_user_data(
    user_id: str = Query(...),
    reason: str = Query(..., min_length=1, max_length=500),
    admin_id: str = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Delete user data for GDPR right to be forgotten."""
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Anonymize user data
        user.email = f"deleted_{user_id}@deleted.local"
        user.password_hash = None
        user.credits = 0
        user.is_active = False
        user.is_deleted = True
        user.deleted_at = datetime.now(timezone.utc)
        user.deletion_reason = reason
        
        db.commit()
        logger.info(f"Admin {admin_id} deleted user data for {user_id}. Reason: {reason}")
        
        return {
            "success": True,
            "message": f"User data deleted for {user_id}",
            "user_id": user_id,
            "deleted_at": user.deleted_at.isoformat() if hasattr(user, 'deleted_at') else None
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Delete user data error: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to delete user data")


@router.get("/data-retention-policy")
async def get_data_retention_policy(
    admin_id: str = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Get data retention policy."""
    return {
        "policy": {
            "user_data": {
                "retention_days": 2555,
                "description": "User account data retained for 7 years after deletion"
            },
            "verification_logs": {
                "retention_days": 1825,
                "description": "Verification logs retained for 5 years"
            },
            "audit_logs": {
                "retention_days": 2555,
                "description": "Audit logs retained for 7 years"
            },
            "api_logs": {
                "retention_days": 365,
                "description": "API access logs retained for 1 year"
            }
        },
        "last_updated": "2025-01-08T00:00:00Z",
        "compliance_standards": ["GDPR", "CCPA", "SOC2"]
    }
