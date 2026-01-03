"""User preferences API endpoints for language and currency."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.user_preference import UserPreference
from app.models.user import User
from app.schemas.responses import SuccessResponse

router = APIRouter(prefix="/api/user/preferences", tags=["preferences"])


@router.get("", response_model=SuccessResponse)
async def get_preferences(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get user language and currency preferences."""
    prefs = db.query(UserPreference).filter(
        UserPreference.user_id == current_user.id
    ).first()
    
    if not prefs:
        return SuccessResponse(
            data={
                "language": "en",
                "currency": "USD"
            }
        )
    
    return SuccessResponse(
        data={
            "language": prefs.language or "en",
            "currency": prefs.currency or "USD"
        }
    )


@router.put("", response_model=SuccessResponse)
async def update_preferences(
    language: str = None,
    currency: str = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update user language and currency preferences."""
    
    # Validate language
    valid_languages = ['en', 'es', 'fr', 'de', 'pt', 'zh', 'ja', 'ar', 'hi', 'yo']
    if language and language not in valid_languages:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid language. Supported: {', '.join(valid_languages)}"
        )
    
    # Validate currency
    valid_currencies = ['USD', 'EUR', 'GBP', 'NGN', 'INR', 'CNY', 'JPY', 'BRL', 'CAD', 'AUD']
    if currency and currency not in valid_currencies:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid currency. Supported: {', '.join(valid_currencies)}"
        )
    
    # Get or create preferences
    prefs = db.query(UserPreference).filter(
        UserPreference.user_id == current_user.id
    ).first()
    
    if not prefs:
        prefs = UserPreference(user_id=current_user.id)
        db.add(prefs)
    
    # Update fields
    if language:
        prefs.language = language
    if currency:
        prefs.currency = currency
    
    db.commit()
    db.refresh(prefs)
    
    return SuccessResponse(
        data={
            "language": prefs.language or "en",
            "currency": prefs.currency or "USD"
        },
        message="Preferences updated successfully"
    )
