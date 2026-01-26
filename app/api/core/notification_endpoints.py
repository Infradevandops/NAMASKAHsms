"""Notification API endpoints."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user_id
from app.models.notification import Notification

router = APIRouter(prefix="/api/notifications", tags=["notifications"])


@router.get("")
async def get_notifications(user_id: str = Depends(get_current_user_id), db: Session = Depends(get_db)):
    """Get user notifications."""
    notifications = (
        db.query(Notification)
        .filter(Notification.user_id == user_id)
        .order_by(Notification.created_at.desc())
        .limit(50)
        .all()
    )

    return {
        "notifications": [n.to_dict() for n in notifications],
        "unread_count": sum(1 for n in notifications if not n.is_read),
    }


@router.post("/{notification_id}/read")
async def mark_notification_read(
    notification_id: str,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Mark notification as read."""
    notification = (
        db.query(Notification).filter(Notification.id == notification_id, Notification.user_id == user_id).first()
    )

    if not notification:
        raise HTTPException(status_code=404, detail="Notification not found")

    notification.is_read = True
    db.commit()

    return {"success": True}


@router.post("/mark-all-read")
async def mark_all_read(user_id: str = Depends(get_current_user_id), db: Session = Depends(get_db)):
    """Mark all notifications as read."""
    db.query(Notification).filter(Notification.user_id == user_id, Notification.is_read is False).update(
        {"is_read": True}
    )

    db.commit()

    return {"success": True}


@router.delete("/{notification_id}")
async def delete_notification(
    notification_id: str,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Delete a notification."""
    notification = (
        db.query(Notification).filter(Notification.id == notification_id, Notification.user_id == user_id).first()
    )

    if not notification:
        raise HTTPException(status_code=404, detail="Notification not found")

    db.delete(notification)
    db.commit()

    return {"success": True}
