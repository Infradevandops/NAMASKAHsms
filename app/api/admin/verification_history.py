"""Admin verification history endpoints."""

import csv
from datetime import datetime, timedelta, timezone
from io import StringIO
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user_id
from app.core.logging import get_logger
from app.models.user import User
from app.models.verification import Verification

logger = get_logger(__name__)
router = APIRouter(prefix="/admin/verifications", tags=["Admin Verification History"])


async def require_admin(user_id: str = Depends(get_current_user_id), db: Session = Depends(get_db)):
    """Verify admin access."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user or not user.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")
    return user_id


@router.get("")
async def list_verifications(
    status: Optional[str] = Query(None),
    country: Optional[str] = Query(None),
    service: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    admin_id: str = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """List verification history with optional filters."""
    try:
        query = db.query(Verification)

        if status:
            valid_statuses = ["pending", "completed", "failed", "expired"]
            if status not in valid_statuses:
                raise HTTPException(status_code=400, detail=f"Invalid status: {status}")
            query = query.filter(Verification.status == status)

        if country:
            query = query.filter(Verification.country == country)

        if service:
            query = query.filter(Verification.service_name == service)

        total = query.count()
        verifications = query.order_by(Verification.created_at.desc()).limit(limit).offset(offset).all()

        return {
            "total": total,
            "limit": limit,
            "offset": offset,
            "verifications": [
                {
                    "id": v.id,
                    "user_id": v.user_id,
                    "country": v.country,
                    "service": v.service_name,
                    "status": v.status,
                    "phone_number": (v.phone_number[:3] + "***" + v.phone_number[-2:] if v.phone_number else None),
                    "created_at": v.created_at.isoformat() if v.created_at else None,
                    "completed_at": (v.completed_at.isoformat() if v.completed_at else None),
                    "cost_usd": float(v.cost or 0),
                }
                for v in verifications
            ],
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"List verifications error: {e}")
        raise HTTPException(status_code=500, detail="Failed to list verifications")


@router.get("/{verification_id}")
async def get_verification_detail(
    verification_id: str,
    admin_id: str = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Get detailed verification info."""
    try:
        verification = db.query(Verification).filter(Verification.id == verification_id).first()
        if not verification:
            raise HTTPException(status_code=404, detail="Verification not found")

        user = db.query(User).filter(User.id == verification.user_id).first()

        return {
            "id": verification.id,
            "user_id": verification.user_id,
            "user_email": user.email if user else None,
            "country": verification.country,
            "service": verification.service_name,
            "status": verification.status,
            "phone_number": verification.phone_number,
            "created_at": (verification.created_at.isoformat() if verification.created_at else None),
            "completed_at": (verification.completed_at.isoformat() if verification.completed_at else None),
            "cost_usd": float(verification.cost or 0),
            "messages_count": (len(verification.messages) if hasattr(verification, "messages") else 0),
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get verification detail error: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch verification")


@router.get("/analytics/summary")
async def get_verification_analytics(
    days: int = Query(30, ge=1, le=365),
    admin_id: str = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Get verification analytics for the last N days."""
    try:
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)

        verifications = db.query(Verification).filter(Verification.created_at >= cutoff_date).all()

        total = len(verifications)
        completed = len([v for v in verifications if v.status == "completed"])
        failed = len([v for v in verifications if v.status == "failed"])
        pending = len([v for v in verifications if v.status == "pending"])

        total_cost = sum(float(v.cost or 0) for v in verifications)

        # Group by country
        by_country = {}
        for v in verifications:
            country = v.country or "Unknown"
            if country not in by_country:
                by_country[country] = 0
            by_country[country] += 1

        # Group by service
        by_service = {}
        for v in verifications:
            service = v.service_name or "Unknown"
            if service not in by_service:
                by_service[service] = 0
            by_service[service] += 1

        return {
            "period_days": days,
            "total_verifications": total,
            "completed": completed,
            "failed": failed,
            "pending": pending,
            "success_rate": round((completed / total * 100) if total > 0 else 0, 2),
            "total_cost_usd": round(total_cost, 2),
            "avg_cost_per_verification": round(total_cost / total if total > 0 else 0, 2),
            "by_country": by_country,
            "by_service": by_service,
        }
    except Exception as e:
        logger.error(f"Get verification analytics error: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch analytics")


@router.post("/export")
async def export_verifications(
    status: Optional[str] = Query(None),
    country: Optional[str] = Query(None),
    days: int = Query(30, ge=1, le=365),
    admin_id: str = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Export verification data as CSV."""
    try:
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)

        query = db.query(Verification).filter(Verification.created_at >= cutoff_date)

        if status:
            query = query.filter(Verification.status == status)

        if country:
            query = query.filter(Verification.country == country)

        verifications = query.all()

        output = StringIO()
        writer = csv.writer(output)
        writer.writerow(
            [
                "ID",
                "User ID",
                "Country",
                "Service",
                "Status",
                "Created At",
                "Completed At",
                "Cost USD",
            ]
        )

        for v in verifications:
            writer.writerow(
                [
                    v.id,
                    v.user_id,
                    v.country,
                    v.service_name,
                    v.status,
                    v.created_at.isoformat() if v.created_at else "",
                    v.completed_at.isoformat() if v.completed_at else "",
                    float(v.cost or 0),
                ]
            )

        logger.info(f"Admin {admin_id} exported {len(verifications)} verifications")

        return {
            "success": True,
            "message": f"Exported {len(verifications)} verifications",
            "csv_data": output.getvalue(),
            "count": len(verifications),
        }
    except Exception as e:
        logger.error(f"Export verifications error: {e}")
        raise HTTPException(status_code=500, detail="Failed to export verifications")
