"""Admin analytics endpoints."""

from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.dependencies import get_current_user_id
from app.models.user import User

router = APIRouter()


async def require_admin(user_id: str = Depends(get_current_user_id), db: Session = Depends(get_db)):
    """Verify admin access."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user or not user.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")
    return user_id


@router.get("/analytics/overview")
async def get_analytics_overview(
    admin_id: str = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Get analytics overview."""
    try:
        return {
            "overview": {
                "total_users": 0,
                "total_verifications": 0,
                "success_rate": 0.0,
                "revenue": 0.0
            },
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get analytics: {str(e)}")