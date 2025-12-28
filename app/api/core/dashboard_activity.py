"""Dashboard activity endpoints."""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.core.database import get_db
from app.core.dependencies import get_current_user_id
from app.models.verification import Verification

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


@router.get("/activity/recent")
async def get_recent_activity(
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """Get recent verification activity for dashboard."""
    verifications = db.query(Verification).filter(
        Verification.user_id == user_id
    ).order_by(desc(Verification.created_at)).limit(10).all()
    
    activities = []
    for v in verifications:
        activities.append({
            "id": v.id,
            "service_name": v.service_name or "Unknown",
            "phone_number": v.phone_number or "N/A",
            "status": v.status or "pending",
            "created_at": v.created_at.isoformat() if v.created_at else None
        })
    
    return {"activities": activities}
