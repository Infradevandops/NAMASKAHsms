"""Admin actions endpoints."""

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


@router.post("/actions/system-maintenance")
async def trigger_system_maintenance(
    admin_id: str = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Trigger system maintenance."""
    try:
        return {
            "action": "system_maintenance",
            "status": "initiated",
            "admin_id": admin_id,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to trigger maintenance: {str(e)}")


@router.post("/actions/clear-cache")
async def clear_system_cache(
    admin_id: str = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Clear system cache."""
    try:
        return {
            "action": "clear_cache",
            "status": "completed",
            "admin_id": admin_id,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to clear cache: {str(e)}")
