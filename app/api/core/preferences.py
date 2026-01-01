"""User preferences API endpoints."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from app.core.dependencies import get_current_user, get_db
from app.models.user import User

router = APIRouter()

class PreferencesUpdate(BaseModel):
    language: str = None
    currency: str = None

SUPPORTED_LANGUAGES = ['en', 'es', 'fr', 'de', 'pt', 'zh', 'ja', 'ar', 'hi']
SUPPORTED_CURRENCIES = ['USD', 'EUR', 'GBP', 'NGN', 'INR', 'CNY', 'JPY', 'BRL', 'CAD', 'AUD']

@router.put("/user/preferences")
async def update_preferences(
    prefs: PreferencesUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update user language and currency preferences."""
    if prefs.language and prefs.language in SUPPORTED_LANGUAGES:
        current_user.language = prefs.language
    elif prefs.language:
        raise HTTPException(400, f"Unsupported language: {prefs.language}")
    
    if prefs.currency and prefs.currency in SUPPORTED_CURRENCIES:
        current_user.currency = prefs.currency
    elif prefs.currency:
        raise HTTPException(400, f"Unsupported currency: {prefs.currency}")
    
    db.commit()
    
    return {
        "success": True,
        "language": current_user.language,
        "currency": current_user.currency
    }

@router.get("/user/preferences")
async def get_preferences(current_user: User = Depends(get_current_user)):
    """Get user preferences."""
    return {
        "language": current_user.language,
        "currency": current_user.currency
    }
