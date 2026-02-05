"""Notification center endpoints for advanced notification management."""


from datetime import datetime, timedelta
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import desc, or_
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.dependencies import get_current_user_id
from app.core.logging import get_logger
from app.models.notification import Notification
from app.models.user import User
import csv
import io

logger = get_logger(__name__)
router = APIRouter(prefix="/api/notifications", tags=["Notification Center"])


@router.get("/center")
async def get_notification_center(
    user_id: str = Depends(get_current_user_id),
    category: Optional[str] = Query(None, description="Filter by notification type"),
    is_read: Optional[bool] = Query(None, description="Filter by read status"),
    date_from: Optional[str] = Query(None, description="Filter from date (YYYY-MM-DD)"),
    date_to: Optional[str] = Query(None, description="Filter to date (YYYY-MM-DD)"),
    sort_by: str = Query("newest", description="Sort by: newest, oldest, unread_first"),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(20, ge=1, le=100, description="Number of records to return"),
    db: Session = Depends(get_db),
):
    """Get notifications with advanced filtering and sorting.

    Query Parameters:
        - category: Filter by notification type (verification, payment, system, etc.)
        - is_read: Filter by read status (true/false)
        - date_from: Filter from date (YYYY-MM-DD)
        - date_to: Filter to date (YYYY-MM-DD)
        - sort_by: Sort order (newest, oldest, unread_first)
        - skip: Pagination offset
        - limit: Pagination limit (max 100)

    Returns:
        - total: Total number of notifications matching filters
        - skip: Number of records skipped
        - limit: Number of records returned
        - notifications: List of notifications
    """
try:
        # Verify user exists
        user = db.query(User).filter(User.id == user_id).first()
if not user:
            raise ValueError(f"User {user_id} not found")

        # Build query
        query = db.query(Notification).filter(Notification.user_id == user_id)

        # Apply filters
if category:
            query = query.filter(Notification.type == category)

if is_read is not None:
            query = query.filter(Notification.is_read == is_read)

if date_from:
try:
                date_from_obj = datetime.strptime(date_from, "%Y-%m-%d")
                query = query.filter(Notification.created_at >= date_from_obj)
except ValueError:
                raise HTTPException(status_code=400, detail="Invalid date_from format (use YYYY-MM-DD)")

if date_to:
try:
                date_to_obj = datetime.strptime(date_to, "%Y-%m-%d") + timedelta(days=1)
                query = query.filter(Notification.created_at < date_to_obj)
except ValueError:
                raise HTTPException(status_code=400, detail="Invalid date_to format (use YYYY-MM-DD)")

        # Get total count before pagination
        total = query.count()

        # Apply sorting
if sort_by == "oldest":
            query = query.order_by(Notification.created_at)
elif sort_by == "unread_first":
            query = query.order_by(Notification.is_read, desc(Notification.created_at))
else:  # newest (default)
            query = query.order_by(desc(Notification.created_at))

        # Apply pagination
        notifications = query.offset(skip).limit(limit).all()

        logger.info(
            f"Retrieved {len(notifications)} notifications for user {user_id} "
            f"(total: {total}, filters: category={category}, is_read={is_read})"
        )

        return {
            "total": total,
            "skip": skip,
            "limit": limit,
            "notifications": [n.to_dict() for n in notifications],
        }

except ValueError as e:
        logger.error(f"Validation error: {str(e)}")
        raise HTTPException(status_code=404, detail=str(e))
except Exception as e:
        logger.error(f"Failed to get notification center: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve notifications",
        )


@router.get("/categories")
async def get_notification_categories(
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Get available notification categories with counts.

    Returns:
        - categories: List of notification types with unread counts
    """
try:
        # Verify user exists
        user = db.query(User).filter(User.id == user_id).first()
if not user:
            raise ValueError(f"User {user_id} not found")

        # Get all notification types for this user
        notifications = db.query(Notification).filter(Notification.user_id == user_id).all()

        # Group by type and count
        categories = {}
for notif in notifications:
if notif.type not in categories:
                categories[notif.type] = {"total": 0, "unread": 0}
            categories[notif.type]["total"] += 1
if not notif.is_read:
                categories[notif.type]["unread"] += 1

        logger.info(f"Retrieved {len(categories)} notification categories for user {user_id}")

        return {"categories": [{"type": k, "total": v["total"], "unread": v["unread"]} for k, v in categories.items()]}

except ValueError as e:
        logger.error(f"Validation error: {str(e)}")
        raise HTTPException(status_code=404, detail=str(e))
except Exception as e:
        logger.error(f"Failed to get notification categories: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve categories",
        )


@router.post("/search")
async def search_notifications(
    user_id: str = Depends(get_current_user_id),
    query: str = Query(..., min_length=2, description="Search query"),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """Search notifications by title or message.

    Query Parameters:
        - query: Search query (minimum 2 characters)
        - skip: Pagination offset
        - limit: Pagination limit (max 100)

    Returns:
        - total: Total search results
        - notifications: Matching notifications
    """
try:
        # Verify user exists
        user = db.query(User).filter(User.id == user_id).first()
if not user:
            raise ValueError(f"User {user_id} not found")

        # Search in title and message
        search_query = f"%{query}%"
        search = db.query(Notification).filter(
            Notification.user_id == user_id,
            or_(
                Notification.title.ilike(search_query),
                Notification.message.ilike(search_query),
            ),
        )

        total = search.count()
        notifications = search.order_by(desc(Notification.created_at)).offset(skip).limit(limit).all()

        logger.info(f"Search for '{query}' returned {len(notifications)} results for user {user_id}")

        return {
            "total": total,
            "skip": skip,
            "limit": limit,
            "query": query,
            "notifications": [n.to_dict() for n in notifications],
        }

except ValueError as e:
        logger.error(f"Validation error: {str(e)}")
        raise HTTPException(status_code=404, detail=str(e))
except Exception as e:
        logger.error(f"Failed to search notifications: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to search notifications",
        )


@router.post("/bulk-read")
async def bulk_mark_as_read(
    user_id: str = Depends(get_current_user_id),
    notification_ids: List[str] = Query(..., description="List of notification IDs to mark as read"),
    db: Session = Depends(get_db),
):
    """Mark multiple notifications as read.

    Query Parameters:
        - notification_ids: List of notification IDs

    Returns:
        - updated: Number of notifications updated
    """
try:
        # Verify user exists
        user = db.query(User).filter(User.id == user_id).first()
if not user:
            raise ValueError(f"User {user_id} not found")

        # Update notifications
        updated = (
            db.query(Notification)
            .filter(
                Notification.user_id == user_id,
                Notification.id.in_(notification_ids),
            )
            .update({"is_read": True})
        )

        db.commit()

        logger.info(f"Marked {updated} notifications as read for user {user_id}")

        return {"updated": updated}

except ValueError as e:
        logger.error(f"Validation error: {str(e)}")
        raise HTTPException(status_code=404, detail=str(e))
except Exception as e:
        logger.error(f"Failed to bulk mark as read: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update notifications",
        )


@router.post("/bulk-delete")
async def bulk_delete_notifications(
    user_id: str = Depends(get_current_user_id),
    notification_ids: List[str] = Query(..., description="List of notification IDs to delete"),
    db: Session = Depends(get_db),
):
    """Delete multiple notifications.

    Query Parameters:
        - notification_ids: List of notification IDs

    Returns:
        - deleted: Number of notifications deleted
    """
try:
        # Verify user exists
        user = db.query(User).filter(User.id == user_id).first()
if not user:
            raise ValueError(f"User {user_id} not found")

        # Delete notifications
        deleted = (
            db.query(Notification)
            .filter(
                Notification.user_id == user_id,
                Notification.id.in_(notification_ids),
            )
            .delete()
        )

        db.commit()

        logger.info(f"Deleted {deleted} notifications for user {user_id}")

        return {"deleted": deleted}

except ValueError as e:
        logger.error(f"Validation error: {str(e)}")
        raise HTTPException(status_code=404, detail=str(e))
except Exception as e:
        logger.error(f"Failed to bulk delete: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete notifications",
        )


@router.get("/export")
async def export_notifications(
    user_id: str = Depends(get_current_user_id),
    format: str = Query("json", description="Export format: json or csv"),
    db: Session = Depends(get_db),
):
    """Export notifications in JSON or CSV format.

    Query Parameters:
        - format: Export format (json or csv)

    Returns:
        - Exported notifications in requested format
    """
try:
        # Verify user exists
        user = db.query(User).filter(User.id == user_id).first()
if not user:
            raise ValueError(f"User {user_id} not found")

        # Get all notifications
        notifications = (
            db.query(Notification).filter(Notification.user_id == user_id).order_by(desc(Notification.created_at)).all()
        )

if format == "csv":

            output = io.StringIO()
            writer = csv.DictWriter(
                output,
                fieldnames=["id", "type", "title", "message", "is_read", "created_at"],
            )
            writer.writeheader()
for n in notifications:
                writer.writerow(
                    {
                        "id": n.id,
                        "type": n.type,
                        "title": n.title,
                        "message": n.message,
                        "is_read": n.is_read,
                        "created_at": n.created_at.isoformat() if n.created_at else None,
                    }
                )
            return {"format": "csv", "data": output.getvalue()}
else:  # json
            return {
                "format": "json",
                "data": [n.to_dict() for n in notifications],
            }

except ValueError as e:
        logger.error(f"Validation error: {str(e)}")
        raise HTTPException(status_code=404, detail=str(e))
except Exception as e:
        logger.error(f"Failed to export notifications: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to export notifications",
        )
