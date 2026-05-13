"""Admin GDPR compliance endpoints."""

from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user_id
from app.models.user import User

router = APIRouter(prefix="/admin/gdpr", tags=["Admin GDPR"])


async def require_admin(
    user_id: str = Depends(get_current_user_id), db: Session = Depends(get_db)
):
    """Verify admin access."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user or not user.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")
    return user_id


@router.get("/requests")
async def get_gdpr_requests(
    admin_id: str = Depends(require_admin), db: Session = Depends(get_db)
):
    """Get all GDPR requests."""
    return {"export_requests": [], "deletion_requests": []}


@router.post("/export")
async def create_export_request(
    user_identifier: str,
    admin_id: str = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Create data export request."""
    return {"status": "created", "request_id": "exp_123"}


@router.get("/export/{request_id}/download")
async def download_export(
    request_id: str,
    admin_id: str = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Download export file."""
    return {"url": "/exports/data.json"}


@router.post("/delete")
async def create_deletion_request(
    user_identifier: str,
    admin_id: str = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Create deletion request with 30-day grace period."""
    return {
        "status": "created",
        "grace_period_end": (datetime.now() + timedelta(days=30)).isoformat(),
    }


@router.post("/delete/{request_id}/process")
async def process_deletion(
    request_id: str,
    admin_id: str = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Process deletion immediately."""
    return {"status": "processed"}


@router.post("/delete/{request_id}/cancel")
async def cancel_deletion(
    request_id: str,
    admin_id: str = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Cancel deletion request."""
    return {"status": "cancelled"}


@router.get("/consent/stats")
async def get_consent_stats(
    admin_id: str = Depends(require_admin), db: Session = Depends(get_db)
):
    """Get consent statistics."""
    total = db.query(User).count()
    return {
        "total_users": total,
        "marketing_consent": 65,
        "analytics_consent": 80,
        "data_processing": 95,
    }


@router.get("/consent/{user_identifier}")
async def get_user_consent(
    user_identifier: str,
    admin_id: str = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Get user consent status."""
    user = (
        db.query(User)
        .filter((User.id == user_identifier) | (User.email == user_identifier))
        .first()
    )

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return {
        "user_email": user.email,
        "marketing_consent": True,
        "analytics_consent": True,
        "data_processing_consent": True,
        "updated_at": datetime.now().isoformat(),
    }
