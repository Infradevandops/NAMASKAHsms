"""Notification endpoints for managing in-app notifications."""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user_id
from app.core.logging import get_logger
from app.services.notification_service import NotificationService

logger = get_logger(__name__)
router = APIRouter(prefix="/notifications", tags=["Notifications"])


@router.get("")
async def get_notifications(
    user_id: str = Depends(get_current_user_id),
    unread_only: bool = Query(False, description="Only return unread notifications"),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(20, ge=1, le=100, description="Number of records to return"),
    db: Session = Depends(get_db),
):
    """Get notifications for user.

    Query Parameters:
        - unread_only: Only return unread notifications (optional)
        - skip: Number of records to skip (pagination)
        - limit: Number of records to return (max 100)

    Returns:
        - total: Total number of notifications
        - skip: Number of records skipped
        - limit: Number of records returned
        - notifications: List of notifications
    """
    try:
        notification_service = NotificationService(db)
        result = notification_service.get_notifications(
            user_id=user_id, unread_only=unread_only, skip=skip, limit=limit
        )

        logger.info(
            f"Retrieved {len(result['notifications'])} notifications for user {user_id}"
        )

        return result

    except ValueError as e:
        logger.error(f"Validation error: {str(e)}")
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to get notifications: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve notifications",
        )


@router.get("/unread-count")
async def get_unread_count(
    user_id: str = Depends(get_current_user_id), db: Session = Depends(get_db)
):
    """Get count of unread notifications for user.

    Returns:
        - unread_count: Number of unread notifications
    """
    try:
        notification_service = NotificationService(db)
        count = notification_service.get_unread_count(user_id)

        logger.info(f"Retrieved unread count for user {user_id}: {count}")

        return {"user_id": user_id, "unread_count": count}

    except ValueError as e:
        logger.error(f"Validation error: {str(e)}")
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to get unread count: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve unread count",
        )


@router.get("/{notification_id}")
async def get_notification(
    notification_id: str,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Get a specific notification.

    Path Parameters:
        - notification_id: Notification ID

    Returns:
        - Notification details
    """
    try:
        notification_service = NotificationService(db)
        notification = notification_service.get_notification(notification_id, user_id)

        logger.info(f"Retrieved notification: {notification_id}")

        return {
            "id": notification.id,
            "type": notification.type,
            "title": notification.title,
            "message": notification.message,
            "data": notification.data,
            "read": notification.read,
            "created_at": (
                notification.created_at.isoformat() if notification.created_at else None
            ),
            "read_at": (
                notification.read_at.isoformat() if notification.read_at else None
            ),
        }

    except ValueError as e:
        logger.error(f"Validation error: {str(e)}")
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to get notification: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve notification",
        )


@router.post("/{notification_id}/read")
async def mark_as_read(
    notification_id: str,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Mark notification as read.

    Path Parameters:
        - notification_id: Notification ID

    Returns:
        - Updated notification details
    """
    try:
        notification_service = NotificationService(db)
        notification = notification_service.mark_as_read(notification_id, user_id)

        logger.info(f"Marked notification as read: {notification_id}")

        return {
            "id": notification.id,
            "read": notification.read,
            "read_at": (
                notification.read_at.isoformat() if notification.read_at else None
            ),
        }

    except ValueError as e:
        logger.error(f"Validation error: {str(e)}")
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to mark notification as read: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to mark notification as read",
        )


@router.post("/read-all")
async def mark_all_as_read(
    user_id: str = Depends(get_current_user_id), db: Session = Depends(get_db)
):
    """Mark all notifications as read for user.

    Returns:
        - count: Number of notifications marked as read
    """
    try:
        notification_service = NotificationService(db)
        count = notification_service.mark_all_as_read(user_id)

        logger.info(f"Marked {count} notifications as read for user {user_id}")

        return {"user_id": user_id, "count": count}

    except ValueError as e:
        logger.error(f"Validation error: {str(e)}")
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(
            f"Failed to mark all notifications as read: {str(e)}", exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to mark notifications as read",
        )


@router.delete("/{notification_id}")
async def delete_notification(
    notification_id: str,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Delete a notification.

    Path Parameters:
        - notification_id: Notification ID

    Returns:
        - success: True if deleted
    """
    try:
        notification_service = NotificationService(db)
        notification_service.delete_notification(notification_id, user_id)

        logger.info(f"Deleted notification: {notification_id}")

        return {"success": True, "message": "Notification deleted"}

    except ValueError as e:
        logger.error(f"Validation error: {str(e)}")
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to delete notification: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete notification",
        )


@router.delete("")
async def delete_all_notifications(
    user_id: str = Depends(get_current_user_id), db: Session = Depends(get_db)
):
    """Delete all notifications for user.

    Returns:
        - count: Number of notifications deleted
    """
    try:
        notification_service = NotificationService(db)
        count = notification_service.delete_all_notifications(user_id)

        logger.info(f"Deleted {count} notifications for user {user_id}")

        return {"user_id": user_id, "count": count}

    except ValueError as e:
        logger.error(f"Validation error: {str(e)}")
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to delete all notifications: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete notifications",
        )
