"""User profile API endpoints."""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.dependencies import get_current_user_id
from app.models.user import User

router = APIRouter(prefix="/api/user", tags=["user"])


@router.get("/me")
async def get_current_user(
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """Get current user profile."""
    user = db.query(User).filter(User.id == user_id).first()
    
    return {
        "id": user.id,
        "email": user.email,
        "is_admin": user.is_admin,
        "is_moderator": user.is_moderator,
        "credits": float(user.credits),
        "subscription_tier": user.subscription_tier
    }
