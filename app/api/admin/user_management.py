"""Admin user management endpoints."""

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


@router.get("/users/list")
async def list_users(
    admin_id: str = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """List users."""
    try:
        users = db.query(User).all()
        return {
            "users": [{"id": u.id, "email": u.email, "tier": getattr(u, 'tier', 'freemium')} for u in users],
            "total": len(users)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list users: {str(e)}")
