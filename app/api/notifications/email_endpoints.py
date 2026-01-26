"""Email notification endpoints."""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user_id
from app.core.logging import get_logger
from app.models.notification_preference import NotificationPreference
from app.models.user import User
from app.services.email_notification_service import EmailNotificationService

logger = get_logger(__name__)
router = APIRouter(prefix="/api/notifications/email", tags=["Email Notifications"])


@router.post("/test")
async def send_test_email(
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Send a test email to verify email configuration.

    Returns:
        - success: Whether email was sent successfully
        - message: Status message
    """
    try:
        # Get user
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        # Send test email
        service = EmailNotificationService(db)
        success = await service.send_notification_email(
            user_email=user.email,
            notification_type="system",
            title="Test Email",
            message="This is a test email from Namaskah SMS. If you received this, email notifications are working correctly!",
        )

        if success:
            logger.info(f"Test email sent to {user.email}")
            return {
                "success": True,
                "message": f"Test email sent to {user.email}",
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to send test email")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error sending test email: {e}")
        raise HTTPException(status_code=500, detail="Failed to send test email")


@router.get("/preferences")
async def get_email_preferences(
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Get user's email notification preferences.

    Returns:
        - email_notifications_enabled: Whether email notifications are enabled
        - notification_types: Email preferences by notification type
    """
    try:
        # Get user
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        # Get preferences
        preferences = db.query(NotificationPreference).filter(NotificationPreference.user_id == user_id).all()

        # Build response
        notification_types = {}
        for pref in preferences:
            delivery_methods = pref.delivery_methods.split(",") if pref.delivery_methods else []
            notification_types[pref.notification_type] = {
                "enabled": pref.enabled,
                "email_enabled": "email" in delivery_methods,
                "frequency": pref.frequency,
            }

        logger.info(f"Retrieved email preferences for user {user_id}")

        return {
            "email_notifications_enabled": True,
            "notification_types": notification_types,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving email preferences: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve email preferences")


@router.put("/preferences")
async def update_email_preferences(
    user_id: str = Depends(get_current_user_id),
    notification_type: str = Query(..., description="Notification type"),
    email_enabled: bool = Query(..., description="Enable/disable email for this type"),
    db: Session = Depends(get_db),
):
    """Update email notification preferences for a specific notification type.

    Query Parameters:
        - notification_type: Type of notification (verification, payment, login, etc.)
        - email_enabled: Whether to enable email for this type

    Returns:
        - success: Whether update was successful
        - message: Status message
    """
    try:
        # Get user
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        # Get or create preference
        preference = (
            db.query(NotificationPreference)
            .filter(
                NotificationPreference.user_id == user_id,
                NotificationPreference.notification_type == notification_type,
            )
            .first()
        )

        if not preference:
            raise HTTPException(status_code=404, detail="Notification preference not found")

        # Update delivery methods
        delivery_methods = preference.delivery_methods.split(",") if preference.delivery_methods else []

        if email_enabled and "email" not in delivery_methods:
            delivery_methods.append("email")
        elif not email_enabled and "email" in delivery_methods:
            delivery_methods.remove("email")

        preference.delivery_methods = ",".join(delivery_methods)
        db.commit()

        logger.info(
            f"Updated email preferences for user {user_id}, type {notification_type}: " f"email_enabled={email_enabled}"
        )

        return {
            "success": True,
            "message": f"Email preferences updated for {notification_type}",
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating email preferences: {e}")
        raise HTTPException(status_code=500, detail="Failed to update email preferences")


@router.post("/unsubscribe")
async def unsubscribe_from_emails(
    user_id: str = Depends(get_current_user_id),
    notification_type: Optional[str] = Query(None, description="Specific type to unsubscribe from"),
    db: Session = Depends(get_db),
):
    """Unsubscribe from email notifications.

    Query Parameters:
        - notification_type: Optional specific type to unsubscribe from (if not provided, unsubscribe from all)

    Returns:
        - success: Whether unsubscribe was successful
        - message: Status message
    """
    try:
        # Get user
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        if notification_type:
            # Unsubscribe from specific type
            preference = (
                db.query(NotificationPreference)
                .filter(
                    NotificationPreference.user_id == user_id,
                    NotificationPreference.notification_type == notification_type,
                )
                .first()
            )

            if preference:
                delivery_methods = preference.delivery_methods.split(",") if preference.delivery_methods else []
                if "email" in delivery_methods:
                    delivery_methods.remove("email")
                preference.delivery_methods = ",".join(delivery_methods)
                db.commit()

            logger.info(f"User {user_id} unsubscribed from email for {notification_type}")
        else:
            # Unsubscribe from all
            preferences = db.query(NotificationPreference).filter(NotificationPreference.user_id == user_id).all()

            for preference in preferences:
                delivery_methods = preference.delivery_methods.split(",") if preference.delivery_methods else []
                if "email" in delivery_methods:
                    delivery_methods.remove("email")
                preference.delivery_methods = ",".join(delivery_methods)

            db.commit()

            logger.info(f"User {user_id} unsubscribed from all email notifications")

        return {
            "success": True,
            "message": "Unsubscribed from email notifications",
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error unsubscribing from emails: {e}")
        raise HTTPException(status_code=500, detail="Failed to unsubscribe from emails")
