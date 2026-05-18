"""GDPR compliance endpoints for data export and account deletion."""

import csv
import io
import json
import logging
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user_id
from app.models.api_key import APIKey
from app.models.audit_log import AuditLog
from app.models.user import User, Webhook
from app.models.verification import Verification
from app.schemas.responses import SuccessResponse

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/gdpr", tags=["GDPR"])


class ConsentUpdateRequest(BaseModel):
    """Consent update request"""

    marketing_emails: Optional[bool] = None
    analytics_tracking: Optional[bool] = None
    data_sharing: Optional[bool] = None


class ConsentResponse(BaseModel):
    """Consent response"""

    marketing_emails: bool
    analytics_tracking: bool
    data_sharing: bool
    updated_at: str


@router.get("/export")
async def export_user_data(
    format: str = Query("json", pattern="^(json|csv|pdf)$"),
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Export all user data in JSON, CSV, or PDF format (GDPR right to data portability)."""
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        verifications = (
            db.query(Verification).filter(Verification.user_id == user_id).all()
        )
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
                    "created_at": (
                        log.created_at.isoformat() if log.created_at else None
                    ),
                }
                for log in audit_logs
            ],
            "export_date": datetime.now(timezone.utc).isoformat(),
        }

        if format == "json":
            return export_data
        elif format == "csv":
            return _export_as_csv(export_data)
        elif format == "pdf":
            return _export_as_pdf(export_data)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error exporting user data for {user_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to export user data")


@router.delete("/account")
async def delete_account(
    user_id: str = Depends(get_current_user_id), db: Session = Depends(get_db)
):
    """Delete user account and all associated data (GDPR right to be forgotten)."""
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        db.query(Verification).filter(Verification.user_id == user_id).delete()
        db.query(AuditLog).filter(AuditLog.user_id == user_id).delete()
        db.query(APIKey).filter(APIKey.user_id == user_id).delete()
        db.query(Webhook).filter(Webhook.user_id == user_id).delete()
        db.delete(user)
        db.commit()

        return SuccessResponse(
            message="Account and all associated data deleted successfully"
        )
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error deleting account for {user_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to delete account")


@router.get("/consent", response_model=ConsentResponse)
async def get_consent(
    user_id: str = Depends(get_current_user_id), db: Session = Depends(get_db)
):
    """Get user consent preferences"""
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        # Get consent from user preferences (assuming these fields exist)
        # If not, return defaults
        return ConsentResponse(
            marketing_emails=getattr(user, "marketing_emails_consent", True),
            analytics_tracking=getattr(user, "analytics_tracking_consent", True),
            data_sharing=getattr(user, "data_sharing_consent", False),
            updated_at=datetime.now(timezone.utc).isoformat(),
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting consent for {user_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to get consent")


@router.put("/consent", response_model=ConsentResponse)
async def update_consent(
    request: ConsentUpdateRequest,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Update user consent preferences"""
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        # Update consent fields
        if request.marketing_emails is not None:
            setattr(user, "marketing_emails_consent", request.marketing_emails)
        if request.analytics_tracking is not None:
            setattr(user, "analytics_tracking_consent", request.analytics_tracking)
        if request.data_sharing is not None:
            setattr(user, "data_sharing_consent", request.data_sharing)

        db.commit()
        db.refresh(user)

        return ConsentResponse(
            marketing_emails=getattr(user, "marketing_emails_consent", True),
            analytics_tracking=getattr(user, "analytics_tracking_consent", True),
            data_sharing=getattr(user, "data_sharing_consent", False),
            updated_at=datetime.now(timezone.utc).isoformat(),
        )
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error updating consent for {user_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to update consent")


@router.get("/retention-policy")
async def get_retention_policy():
    """Get data retention policy information"""
    return {
        "policy": {
            "user_data": {
                "retention_period": "Account lifetime + 30 days after deletion",
                "categories": [
                    "Profile information",
                    "Email address",
                    "Authentication data",
                ],
            },
            "verification_data": {
                "retention_period": "90 days",
                "categories": [
                    "Phone numbers",
                    "SMS codes",
                    "Verification status",
                    "Service names",
                ],
            },
            "transaction_data": {
                "retention_period": "7 years (legal requirement)",
                "categories": [
                    "Payment records",
                    "Credit transactions",
                    "Invoices",
                ],
            },
            "audit_logs": {
                "retention_period": "1 year",
                "categories": [
                    "Login events",
                    "API access",
                    "Security events",
                ],
            },
        },
        "deletion_schedule": {
            "automated": "Data is automatically deleted after retention period expires",
            "manual": "Users can request immediate deletion via account deletion",
        },
        "last_updated": "2026-05-17",
    }


def _export_as_csv(data: dict) -> StreamingResponse:
    """Export data as CSV"""
    output = io.StringIO()
    writer = csv.writer(output)

    # Write user data
    writer.writerow(["User Data"])
    writer.writerow(["Field", "Value"])
    for key, value in data["user"].items():
        writer.writerow([key, value])
    writer.writerow([])

    # Write verifications
    writer.writerow(["Verifications"])
    if data["verifications"]:
        writer.writerow(data["verifications"][0].keys())
        for v in data["verifications"]:
            writer.writerow(v.values())
    writer.writerow([])

    # Write audit logs
    writer.writerow(["Audit Logs"])
    if data["audit_logs"]:
        writer.writerow(data["audit_logs"][0].keys())
        for log in data["audit_logs"]:
            writer.writerow(log.values())

    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={
            "Content-Disposition": f"attachment; filename=user-data-{datetime.now().strftime('%Y%m%d')}.csv"
        },
    )


def _export_as_pdf(data: dict) -> StreamingResponse:
    """Export data as PDF (simplified text-based PDF)"""
    # For now, return as plain text with PDF extension
    # In production, use a library like reportlab
    output = io.StringIO()

    output.write("USER DATA EXPORT\n")
    output.write("=" * 50 + "\n\n")

    output.write("User Information:\n")
    for key, value in data["user"].items():
        output.write(f"  {key}: {value}\n")
    output.write("\n")

    output.write(f"Verifications ({len(data['verifications'])}):\n")
    for i, v in enumerate(data["verifications"][:10], 1):
        output.write(f"  {i}. {v['service']} - {v['status']} ({v['created_at']})\n")
    if len(data["verifications"]) > 10:
        output.write(f"  ... and {len(data['verifications']) - 10} more\n")
    output.write("\n")

    output.write(f"Audit Logs ({len(data['audit_logs'])}):\n")
    for i, log in enumerate(data["audit_logs"][:10], 1):
        output.write(
            f"  {i}. {log['event']} from {log['ip_address']} ({log['created_at']})\n"
        )
    if len(data["audit_logs"]) > 10:
        output.write(f"  ... and {len(data['audit_logs']) - 10} more\n")

    output.write("\n" + "=" * 50 + "\n")
    output.write(f"Export Date: {data['export_date']}\n")

    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="application/pdf",
        headers={
            "Content-Disposition": f"attachment; filename=user-data-{datetime.now().strftime('%Y%m%d')}.pdf"
        },
    )
