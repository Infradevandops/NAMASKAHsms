"""User settings management endpoints."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.core.database import get_db
from app.core.dependencies import get_current_user_id
from app.core.logging import get_logger
from app.models.user_preference import UserPreference
from app.models.user import User

logger = get_logger(__name__)
router = APIRouter(prefix="/api/user", tags=["User Settings"])


class UserSettingsUpdate(BaseModel):
    """User settings update model."""

    email_notifications: bool = True
    sms_alerts: bool = False


@router.get("/settings")
async def get_user_settings(
    user_id: str = Depends(get_current_user_id), db: Session = Depends(get_db)
):
    """Get user settings."""
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        # Get or create preferences
        prefs = db.query(UserPreference).filter(UserPreference.user_id == user_id).first()
        if not prefs:
            prefs = UserPreference(user_id=user_id, email_notifications=True, sms_alerts=False)
            db.add(prefs)
            db.commit()
            db.refresh(prefs)

        return {"email_notifications": prefs.email_notifications, "sms_alerts": prefs.sms_alerts}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get settings: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve settings")


@router.put("/settings")
async def update_user_settings(
    settings: UserSettingsUpdate,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Update user settings."""
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        # Get or create preferences
        prefs = db.query(UserPreference).filter(UserPreference.user_id == user_id).first()
        if not prefs:
            prefs = UserPreference(user_id=user_id)
            db.add(prefs)

        # Update settings
        prefs.email_notifications = settings.email_notifications
        prefs.sms_alerts = settings.sms_alerts

        db.commit()

        logger.info(f"Settings updated for user {user_id}")

        return {
            "success": True,
            "message": "Settings updated successfully",
            "settings": {
                "email_notifications": prefs.email_notifications,
                "sms_alerts": prefs.sms_alerts,
            },
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update settings: {str(e)}")
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to update settings")
