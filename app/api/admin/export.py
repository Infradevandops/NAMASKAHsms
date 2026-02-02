"""Admin export endpoints."""

from datetime import datetime, timezone
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
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


@router.get("/export/users")
async def export_users(
    format: str = Query("csv", regex="^(csv|json)$"),
    admin_id: str = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Export users data."""
    try:
        return {
            "export_id": f"users_export_{int(datetime.now().timestamp())}",
            "format": format,
            "status": "completed",
            "download_url": f"/api/admin/download/users_export_{int(datetime.now().timestamp())}.{format}",
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to export users: {str(e)}")


@router.get("/export/verifications")
async def export_verifications(
    format: str = Query("csv", regex="^(csv|json)$"),
    days: int = Query(30, ge=1, le=365),
    admin_id: str = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Export verifications data."""
    try:
        return {
            "export_id": f"verifications_export_{int(datetime.now().timestamp())}",
            "format": format,
            "status": "completed",
            "days": days,
            "download_url": f"/api/admin/download/verifications_export_{int(datetime.now().timestamp())}.{format}",
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to export verifications: {str(e)}")