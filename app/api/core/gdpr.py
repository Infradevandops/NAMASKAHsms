"""GDPR compliance endpoints for data export and account deletion."""
from app.core.dependencies import get_current_user_id
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime

from app.core.database import get_db

router = APIRouter(prefix="/gdpr", tags=["GDPR"])


@router.get("/export")
async def export_user_data(
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """Export all user data in JSON format (GDPR right to data portability)."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")


    verifications = db.query(Verification).filter(Verification.user_id == user_id).all()
    audit_logs = db.query(AuditLog).filter(AuditLog.user_id == user_id).all()

    export_data = {
        "user": {
            "id": user.id,
            "email": user.email,
            "credits": float(user.credits or 0),
            "free_verifications": float(user.free_verifications or 0),
            "is_admin": user.is_admin,
            "email_verified": user.email_verified,
            "referral_code": user.referral_code,
            "created_at": user.created_at.isoformat() if user.created_at else None,
            "provider": user.provider,
        },
        "verifications": [
            {
                "id": v.id,
                "service": v.service,
                "country": v.country,
                "status": v.status,
                "created_at": v.created_at.isoformat() if v.created_at else None,
            }
            for v in verifications
        ],
        "audit_logs": [
            {
                "event": log.event,
                "ip_address": log.ip_address,
                "created_at": log.created_at.isoformat() if log.created_at else None,
            }
            for log in audit_logs
        ],
        "export_date": datetime.utcnow().isoformat(),
    }

    return export_data


@router.delete("/account")
async def delete_account(
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """Delete user account and all associated data (GDPR right to be forgotten)."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")


    db.query(Verification).filter(Verification.user_id == user_id).delete()
    db.query(AuditLog).filter(AuditLog.user_id == user_id).delete()
    db.query(APIKey).filter(APIKey.user_id == user_id).delete()
    db.query(Webhook).filter(Webhook.user_id == user_id).delete()
    db.delete(user)
    db.commit()

    return SuccessResponse(message="Account and all associated data deleted successfully")
