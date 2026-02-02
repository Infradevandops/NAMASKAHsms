"""Admin tier management endpoints."""

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


@router.get("/tiers/list")
async def list_tiers(
    admin_id: str = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """List tiers."""
    try:
        return {
            "tiers": [
                {"name": "freemium", "price": 0},
                {"name": "payg", "price": 0},
                {"name": "pro", "price": 25},
                {"name": "custom", "price": 35}
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list tiers: {str(e)}")