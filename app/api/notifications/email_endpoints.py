"""Email notification endpoints — backed by EmailPreferencePolicy."""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user_id
from app.core.logging import get_logger
from app.models.user import User
from app.services.email_preference_policy import EmailPreferencePolicy

logger = get_logger(__name__)
router = APIRouter(prefix="/api/notifications/email", tags=["Email Notifications"])


@router.post("/test")
async def send_test_email(
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Send a test email to verify email configuration (user-initiated diagnostic)."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    try:
        from app.services.email_service import email_service

        class _TestNotif:
            title = "Test Email"
            message = "Email notifications are working correctly."
            type = "system"
            link = None

        success = await email_service.send_notification_email(
            user_email=user.email,
            notification=_TestNotif(),
            user_name=getattr(user, "display_name", None) or user.email.split("@")[0],
        )
        if not success:
            raise HTTPException(status_code=500, detail="Failed to send test email")
        logger.info(f"Test email sent to {user.email} by user {user_id}")
        return {"success": True, "message": f"Test email sent to {user.email}"}
    except HTTPException:
        raise
    except Exception as exc:
        logger.error(f"Test email error for {user_id}: {exc}")
        raise HTTPException(status_code=500, detail="Failed to send test email")


@router.get("/preferences")
async def get_email_preferences(
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """
    Get user's email notification preferences.

    email_notifications_enabled is derived from actual preference data,
    not hardcoded to True.
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    policy = EmailPreferencePolicy(db)
    return policy.get_effective_preferences(user_id)


@router.put("/preferences")
async def update_email_preferences(
    user_id: str = Depends(get_current_user_id),
    notification_type: str = Query(..., description="Notification type"),
    email_enabled: bool = Query(..., description="Enable/disable email for this type"),
    db: Session = Depends(get_db),
):
    """
    Update email notification preferences.

    Updates both delivery_methods AND the category enabled flag atomically.
    Returns 404 if the preference row does not exist.
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    policy = EmailPreferencePolicy(db)
    updated = policy.set_email_enabled(user_id, notification_type, email_enabled)
    if not updated:
        raise HTTPException(
            status_code=404,
            detail=f"Notification preference not found for type '{notification_type}'",
        )

    logger.info(
        f"Email preference updated: user={user_id} type={notification_type} "
        f"email_enabled={email_enabled}"
    )
    return {
        "success": True,
        "message": f"Email preferences updated for {notification_type}",
    }


@router.post("/unsubscribe")
async def unsubscribe_from_emails(
    user_id: str = Depends(get_current_user_id),
    notification_type: Optional[str] = Query(
        None, description="Specific type to unsubscribe from (omit for all)"
    ),
    db: Session = Depends(get_db),
):
    """Unsubscribe from optional email notifications."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    policy = EmailPreferencePolicy(db)

    if notification_type:
        updated = policy.set_email_enabled(user_id, notification_type, False)
        if not updated:
            raise HTTPException(
                status_code=404,
                detail=f"Preference not found for type '{notification_type}'",
            )
        logger.info(f"User {user_id} unsubscribed from email for {notification_type}")
    else:
        count = policy.unsubscribe_all_optional(user_id)
        logger.info(f"User {user_id} unsubscribed from all email ({count} categories)")

    return {"success": True, "message": "Unsubscribed from email notifications"}
