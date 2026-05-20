import logging

logger = logging.getLogger(__name__)
"""Notification API endpoints."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user_id
from app.models.notification import Notification

router = APIRouter(prefix="/api/notifications", tags=["notifications"])


@router.get("")
async def list_notifications(
    limit: int = 10,
    offset: int = 0,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    try:
        """List user notifications."""
        notifications = (
            db.query(Notification)
            .filter(Notification.user_id == user_id)
            .order_by(Notification.created_at.desc())
            .limit(limit)
            .offset(offset)
            .all()
        )

        unread_count = (
            db.query(Notification)
            .filter(Notification.user_id == user_id, Notification.is_read is False)
            .count()
        )

        total = db.query(Notification).filter(Notification.user_id == user_id).count()

        return {
            "notifications": [n.to_dict() for n in notifications],
            "unread_count": unread_count,
            "total": total,
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in list_notifications: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/unread")
async def get_unread_count(
    user_id: str = Depends(get_current_user_id), db: Session = Depends(get_db)
):
    try:
        """Get unread notification count."""
        count = (
            db.query(Notification)
            .filter(Notification.user_id == user_id, Notification.is_read is False)
            .count()
        )

        return {"count": count}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in get_unread_count: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/{notification_id}/read")
async def mark_as_read(
    notification_id: str,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    try:
        """Mark notification as read."""
        notification = (
            db.query(Notification)
            .filter(Notification.id == notification_id, Notification.user_id == user_id)
            .first()
        )

        if not notification:
            raise HTTPException(status_code=404, detail="Notification not found")

        notification.is_read = True
        db.commit()

        return {"success": True, "message": "Notification marked as read"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in mark_as_read: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/read-all")
async def mark_all_read(
    user_id: str = Depends(get_current_user_id), db: Session = Depends(get_db)
):
    try:
        """Mark all notifications as read."""
        db.query(Notification).filter(
            Notification.user_id == user_id, Notification.is_read is False
        ).update({"is_read": True})

        db.commit()

        return {"success": True, "message": "All notifications marked as read"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in mark_all_read: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.delete("/{notification_id}")
async def delete_notification(
    notification_id: str,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    try:
        """Delete notification."""
        notification = (
            db.query(Notification)
            .filter(Notification.id == notification_id, Notification.user_id == user_id)
            .first()
        )

        if not notification:
            raise HTTPException(status_code=404, detail="Notification not found")

        db.delete(notification)
        db.commit()

        return {"success": True, "message": "Notification deleted"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in delete_notification: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


# Helper function to create notifications


def create_notification(
    db: Session,
    user_id: str,
    type: str,
    title: str,
    message: str = None,
    link: str = None,
    icon: str = None,
):
    """Create a new notification."""
    notification = Notification(
        user_id=user_id, type=type, title=title, message=message, link=link, icon=icon
    )
    db.add(notification)
    db.commit()
    return notification
