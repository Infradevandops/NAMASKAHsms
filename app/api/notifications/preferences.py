"""Notification preferences endpoints for user customization."""


from datetime import time
from typing import List, Optional
from fastapi import APIRouter, Body, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.dependencies import get_current_user_id
from app.core.logging import get_logger
from app.models.notification_preference import NotificationPreference, NotificationPreferenceDefaults
from app.models.user import User

logger = get_logger(__name__)
router = APIRouter(prefix="/api/notifications/preferences", tags=["Notification Preferences"])


# Pydantic models for request/response

class PreferenceUpdate(BaseModel):

    """Update notification preference."""

    notification_type: str = Field(..., description="Type of notification")
    enabled: bool = Field(default=True, description="Enable/disable this notification type")
    delivery_methods: List[str] = Field(default=["toast"], description="Delivery methods: toast, email, sms, webhook")
    quiet_hours_start: Optional[str] = Field(None, description="Quiet hours start (HH:MM)")
    quiet_hours_end: Optional[str] = Field(None, description="Quiet hours end (HH:MM)")
    frequency: str = Field(default="instant", description="Frequency: instant, daily, weekly, never")
    created_at_override: bool = Field(default=False, description="Allow override of quiet hours")


class PreferenceResponse(BaseModel):

    """Notification preference response."""

    id: str
    notification_type: str
    enabled: bool
    delivery_methods: List[str]
    quiet_hours_start: Optional[str]
    quiet_hours_end: Optional[str]
    frequency: str
    created_at_override: bool


    @router.get("")
    async def get_preferences(
        user_id: str = Depends(get_current_user_id),
        notification_type: Optional[str] = Query(None, description="Filter by notification type"),
        db: Session = Depends(get_db),
        ):
        """Get notification preferences for user.

        Query Parameters:
        - notification_type: Optional filter by specific notification type

        Returns:
        - preferences: List of user notification preferences
        - defaults: Default preferences for all notification types
        """
        try:
        # Verify user exists
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise ValueError(f"User {user_id} not found")

        # Get user preferences
        query = db.query(NotificationPreference).filter(NotificationPreference.user_id == user_id)

        if notification_type:
            query = query.filter(NotificationPreference.notification_type == notification_type)

        preferences = query.all()

        # Get all defaults
        defaults = db.query(NotificationPreferenceDefaults).all()

        logger.info(f"Retrieved {len(preferences)} preferences for user {user_id}")

        return {
            "preferences": [p.to_dict() for p in preferences],
            "defaults": [d.to_dict() for d in defaults],
        }

        except ValueError as e:
        logger.error(f"Validation error: {str(e)}")
        raise HTTPException(status_code=404, detail=str(e))
        except Exception as e:
        logger.error(f"Failed to get preferences: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve preferences",
        )


        @router.put("")
    async def update_preferences(
        user_id: str = Depends(get_current_user_id),
        preferences: List[PreferenceUpdate] = Body(..., description="List of preferences to update"),
        db: Session = Depends(get_db),
        ):
        """Update notification preferences for user.

        Request Body:
        - preferences: List of preference updates

        Returns:
        - updated: Number of preferences updated
        - created: Number of preferences created
        """
        try:
        # Verify user exists
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise ValueError(f"User {user_id} not found")

        updated_count = 0
        created_count = 0

        for pref in preferences:
            # Parse quiet hours
            quiet_hours_start = None
            quiet_hours_end = None

        if pref.quiet_hours_start:
        try:
                    quiet_hours_start = time.fromisoformat(pref.quiet_hours_start)
        except ValueError:
                    raise HTTPException(
                        status_code=400,
                        detail=f"Invalid quiet_hours_start format: {pref.quiet_hours_start}",
                    )

        if pref.quiet_hours_end:
        try:
                    quiet_hours_end = time.fromisoformat(pref.quiet_hours_end)
        except ValueError:
                    raise HTTPException(
                        status_code=400,
                        detail=f"Invalid quiet_hours_end format: {pref.quiet_hours_end}",
                    )

            # Check if preference exists
            existing = (
                db.query(NotificationPreference)
                .filter(
                    NotificationPreference.user_id == user_id,
                    NotificationPreference.notification_type == pref.notification_type,
                )
                .first()
            )

        if existing:
                existing.enabled = pref.enabled
                existing.delivery_methods = ",".join(pref.delivery_methods)
                existing.quiet_hours_start = quiet_hours_start
                existing.quiet_hours_end = quiet_hours_end
                existing.frequency = pref.frequency
                existing.created_at_override = pref.created_at_override
                updated_count += 1
        else:
                new_pref = NotificationPreference(
                    user_id=user_id,
                    notification_type=pref.notification_type,
                    enabled=pref.enabled,
                    delivery_methods=",".join(pref.delivery_methods),
                    quiet_hours_start=quiet_hours_start,
                    quiet_hours_end=quiet_hours_end,
                    frequency=pref.frequency,
                    created_at_override=pref.created_at_override,
                )
                db.add(new_pref)
                created_count += 1

        db.commit()

        logger.info(f"Updated {updated_count} and created {created_count} preferences for user {user_id}")

        return {
            "updated": updated_count,
            "created": created_count,
            "total": updated_count + created_count,
        }

        except ValueError as e:
        logger.error(f"Validation error: {str(e)}")
        raise HTTPException(status_code=404, detail=str(e))
        except Exception as e:
        logger.error(f"Failed to update preferences: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update preferences",
        )


        @router.post("/reset")
    async def reset_preferences(
        user_id: str = Depends(get_current_user_id),
        db: Session = Depends(get_db),
        ):
        """Reset notification preferences to defaults.

        Returns:
        - reset: Number of preferences reset
        """
        try:
        # Verify user exists
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise ValueError(f"User {user_id} not found")

        # Delete all user preferences
        deleted = db.query(NotificationPreference).filter(NotificationPreference.user_id == user_id).delete()

        db.commit()

        logger.info(f"Reset {deleted} preferences for user {user_id}")

        return {"reset": deleted}

        except ValueError as e:
        logger.error(f"Validation error: {str(e)}")
        raise HTTPException(status_code=404, detail=str(e))
        except Exception as e:
        logger.error(f"Failed to reset preferences: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to reset preferences",
        )


        @router.get("/defaults")
    async def get_default_preferences(
        db: Session = Depends(get_db),
        ):
        """Get default notification preferences for all notification types.

        Returns:
        - defaults: List of default preferences
        """
        try:
        defaults = db.query(NotificationPreferenceDefaults).all()

        logger.info(f"Retrieved {len(defaults)} default preferences")

        return {
            "defaults": [d.to_dict() for d in defaults],
        }

        except Exception as e:
        logger.error(f"Failed to get default preferences: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve default preferences",
        )


        @router.post("/defaults")
    async def create_default_preference(
        notification_type: str = Query(..., description="Notification type"),
        enabled: bool = Query(True, description="Enabled by default"),
        delivery_methods: str = Query("toast", description="Default delivery methods (comma-separated)"),
        frequency: str = Query("instant", description="Default frequency"),
        description: str = Query(None, description="Description"),
        db: Session = Depends(get_db),
        ):
        """Create or update default notification preference.

        Query Parameters:
        - notification_type: Type of notification
        - enabled: Enabled by default
        - delivery_methods: Default delivery methods
        - frequency: Default frequency
        - description: Description

        Returns:
        - default: Created/updated default preference
        """
        try:
        # Check if exists
        existing = (
            db.query(NotificationPreferenceDefaults)
            .filter(NotificationPreferenceDefaults.notification_type == notification_type)
            .first()
        )

        if existing:
            existing.enabled = enabled
            existing.delivery_methods = delivery_methods
            existing.frequency = frequency
            existing.description = description
        else:
            new_default = NotificationPreferenceDefaults(
                notification_type=notification_type,
                enabled=enabled,
                delivery_methods=delivery_methods,
                frequency=frequency,
                description=description,
            )
            db.add(new_default)

        db.commit()

        logger.info(f"Created/updated default preference for {notification_type}")

        return {"status": "success"}

        except Exception as e:
        logger.error(f"Failed to create default preference: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create default preference",
        )