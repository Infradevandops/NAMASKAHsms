"""Dashboard activity endpoints."""

from fastapi import APIRouter, Depends
from sqlalchemy import desc, func
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user_id
from app.models.verification import Verification

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


@router.get("/activity")
async def get_recent_activity(
    page: int = 1,
    limit: int = 10,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    return await _get_activity_internal(user_id, db, page, limit)


@router.get("/activity/recent")
async def get_recent_activity_list(
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    result = await _get_activity_internal(user_id, db, 1, 10)
    return result["verifications"]


async def _get_activity_internal(user_id: str, db: Session, page: int, limit: int):
    offset = (page - 1) * limit
    try:
        verifications = (
            db.query(Verification)
            .filter(Verification.user_id == user_id)
            .order_by(desc(Verification.created_at))
            .limit(limit)
            .offset(offset)
            .all()
        )
        total = (
            db.query(func.count(Verification.id))
            .filter(Verification.user_id == user_id)
            .scalar()
            or 0
        )
        return {
            "verifications": [
                {
                    "id": str(v.id),
                    "service_name": v.service_name or "Unknown",
                    "phone_number": v.phone_number or "N/A",
                    "status": v.status or "pending",
                    "cost": float(v.cost) if v.cost else 0.0,
                    "created_at": v.created_at.isoformat() if v.created_at else None,
                }
                for v in verifications
            ],
            "total": total,
            "page": page,
            "limit": limit,
        }
    except Exception:
        return {"verifications": [], "total": 0, "page": page, "limit": limit}
