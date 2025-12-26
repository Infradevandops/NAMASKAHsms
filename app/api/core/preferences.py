"""User preferences endpoints"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.core.database import get_db
from app.core.dependencies import get_current_user_id
from app.models.user import User

router = APIRouter(prefix="/api/user", tags=["preferences"])


class PreferencesUpdate(BaseModel):
    language: str
    currency: str


@router.put("/preferences")
async def update_preferences(
    data: PreferencesUpdate,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """Update user language and currency preferences"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    user.language = data.language
    user.currency = data.currency
    db.commit()
    
    return {"success": True, "language": data.language, "currency": data.currency}


@router.get("/preferences")
async def get_preferences(
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """Get user language and currency preferences"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return {
        "language": user.language or "en",
        "currency": user.currency or "USD"
    }
