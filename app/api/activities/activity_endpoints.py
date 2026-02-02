"""Activity feed endpoints for user activity tracking."""


from datetime import datetime, timedelta
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.dependencies import get_current_user_id
from app.core.logging import get_logger
from app.models.activity import Activity
from app.models.user import User
from app.services.activity_service import ActivityService
from sqlalchemy import desc
import csv
import io

logger = get_logger(__name__)
router = APIRouter(prefix="/api/activities", tags=["Activity Feed"])


@router.get("")
async def get_activities(
    user_id: str = Depends(get_current_user_id),
    activity_type: Optional[str] = Query(None, description="Filter by activity type"),
    resource_type: Optional[str] = Query(None, description="Filter by resource type"),
    status: Optional[str] = Query(None, description="Filter by status"),
    date_from: Optional[str] = Query(None, description="Filter from date (YYYY-MM-DD)"),
    date_to: Optional[str] = Query(None, description="Filter to date (YYYY-MM-DD)"),
    sort_by: str = Query("newest", description="Sort by: newest, oldest"),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(20, ge=1, le=100, description="Number of records to return"),
    db: Session = Depends(get_db),
):
    """Get user activities with filtering and pagination.

    Query Parameters:
        - activity_type: Filter by activity type (verification, payment, login, settings, api_key)
        - resource_type: Filter by resource type (verification, payment, user, api_key)
        - status: Filter by status (completed, pending, failed)
        - date_from: Filter from date (YYYY-MM-DD)
        - date_to: Filter to date (YYYY-MM-DD)
        - sort_by: Sort order (newest, oldest)
        - skip: Pagination offset
        - limit: Pagination limit (max 100)

    Returns:
        - total: Total number of activities matching filters
        - skip: Number of records skipped
        - limit: Number of records returned
        - activities: List of activities
    """
try:
        # Verify user exists
        user = db.query(User).filter(User.id == user_id).first()
if not user:
            raise HTTPException(status_code=404, detail="User not found")

        # Build query
        query = db.query(Activity).filter(Activity.user_id == user_id)

        # Apply filters
if activity_type:
            query = query.filter(Activity.activity_type == activity_type)

if resource_type:
            query = query.filter(Activity.resource_type == resource_type)

if status:
            query = query.filter(Activity.status == status)

if date_from:
try:
                date_from_obj = datetime.strptime(date_from, "%Y-%m-%d")
                query = query.filter(Activity.created_at >= date_from_obj)
except ValueError:
                raise HTTPException(status_code=400, detail="Invalid date_from format (use YYYY-MM-DD)")

if date_to:
try:
                date_to_obj = datetime.strptime(date_to, "%Y-%m-%d") + timedelta(days=1)
                query = query.filter(Activity.created_at < date_to_obj)
except ValueError:
                raise HTTPException(status_code=400, detail="Invalid date_to format (use YYYY-MM-DD)")

        # Get total count
        total = query.count()

        # Apply sorting
if sort_by == "oldest":
            query = query.order_by(Activity.created_at)
else:  # newest (default)

            query = query.order_by(desc(Activity.created_at))

        # Apply pagination
        activities = query.offset(skip).limit(limit).all()

        logger.info(
            f"Retrieved {len(activities)} activities for user {user_id} "
            f"(total: {total}, filters: type={activity_type}, resource={resource_type}, status={status})"
        )

        return {
            "total": total,
            "skip": skip,
            "limit": limit,
            "activities": [a.to_dict() for a in activities],
        }

except HTTPException:
        raise
except Exception as e:
        logger.error(f"Error retrieving activities for user {user_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve activities")


@router.get("/{activity_id}")
async def get_activity(
    activity_id: str,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Get activity details by ID.

    Args:
        activity_id: Activity ID

    Returns:
        Activity details
    """
try:
        # Verify user exists
        user = db.query(User).filter(User.id == user_id).first()
if not user:
            raise HTTPException(status_code=404, detail="User not found")

        # Get activity
        activity = db.query(Activity).filter(Activity.id == activity_id, Activity.user_id == user_id).first()

if not activity:
            raise HTTPException(status_code=404, detail="Activity not found")

        logger.info(f"Retrieved activity {activity_id} for user {user_id}")

        return activity.to_dict()

except HTTPException:
        raise
except Exception as e:
        logger.error(f"Error retrieving activity {activity_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve activity")


@router.get("/resource/{resource_type}/{resource_id}")
async def get_resource_activities(
    resource_type: str,
    resource_id: str,
    user_id: str = Depends(get_current_user_id),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """Get all activities for a specific resource.

    Args:
        resource_type: Type of resource (verification, payment, user, api_key)
        resource_id: ID of resource
        skip: Pagination offset
        limit: Pagination limit

    Returns:
        List of activities for the resource
    """
try:
        # Verify user exists
        user = db.query(User).filter(User.id == user_id).first()
if not user:
            raise HTTPException(status_code=404, detail="User not found")

        # Build query
        query = (
            db.query(Activity)
            .filter(
                Activity.user_id == user_id,
                Activity.resource_type == resource_type,
                Activity.resource_id == resource_id,
            )
            .order_by(Activity.created_at.desc())
        )

        # Get total count
        total = query.count()

        # Apply pagination
        activities = query.offset(skip).limit(limit).all()

        logger.info(
            f"Retrieved {len(activities)} activities for resource {resource_type}/{resource_id} " f"for user {user_id}"
        )

        return {
            "total": total,
            "skip": skip,
            "limit": limit,
            "activities": [a.to_dict() for a in activities],
        }

except HTTPException:
        raise
except Exception as e:
        logger.error(f"Error retrieving resource activities: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve resource activities")


@router.get("/summary/overview")
async def get_activity_summary(
    user_id: str = Depends(get_current_user_id),
    days: int = Query(30, ge=1, le=365, description="Number of days to include"),
    db: Session = Depends(get_db),
):
    """Get activity summary for user.

    Query Parameters:
        - days: Number of days to include (1-365, default 30)

    Returns:
        - total_activities: Total number of activities
        - by_type: Count of activities by type
        - by_status: Count of activities by status
        - by_resource: Count of activities by resource type
    """
try:
        # Verify user exists
        user = db.query(User).filter(User.id == user_id).first()
if not user:
            raise HTTPException(status_code=404, detail="User not found")

        # Use service to get summary
        service = ActivityService(db)
        summary = service.get_activity_summary(user_id, days)

        logger.info(f"Retrieved activity summary for user {user_id} (last {days} days)")

        return summary

except HTTPException:
        raise
except Exception as e:
        logger.error(f"Error retrieving activity summary for user {user_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve activity summary")


@router.post("/export")
async def export_activities(
    user_id: str = Depends(get_current_user_id),
    activity_type: Optional[str] = Query(None),
    resource_type: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    date_from: Optional[str] = Query(None),
    date_to: Optional[str] = Query(None),
    format: str = Query("json", description="Export format: json or csv"),
    db: Session = Depends(get_db),
):
    """Export activities as JSON or CSV.

    Query Parameters:
        - activity_type: Filter by activity type
        - resource_type: Filter by resource type
        - status: Filter by status
        - date_from: Filter from date (YYYY-MM-DD)
        - date_to: Filter to date (YYYY-MM-DD)
        - format: Export format (json or csv)

    Returns:
        Exported activities in requested format
    """
try:
        # Verify user exists
        user = db.query(User).filter(User.id == user_id).first()
if not user:
            raise HTTPException(status_code=404, detail="User not found")

        # Build query
        query = db.query(Activity).filter(Activity.user_id == user_id)

        # Apply filters
if activity_type:
            query = query.filter(Activity.activity_type == activity_type)

if resource_type:
            query = query.filter(Activity.resource_type == resource_type)

if status:
            query = query.filter(Activity.status == status)

if date_from:
try:
                date_from_obj = datetime.strptime(date_from, "%Y-%m-%d")
                query = query.filter(Activity.created_at >= date_from_obj)
except ValueError:
                raise HTTPException(status_code=400, detail="Invalid date_from format (use YYYY-MM-DD)")

if date_to:
try:
                date_to_obj = datetime.strptime(date_to, "%Y-%m-%d") + timedelta(days=1)
                query = query.filter(Activity.created_at < date_to_obj)
except ValueError:
                raise HTTPException(status_code=400, detail="Invalid date_to format (use YYYY-MM-DD)")

        # Get all matching activities
        activities = query.order_by(Activity.created_at.desc()).all()

if format == "csv":

            output = io.StringIO()
            writer = csv.DictWriter(
                output,
                fieldnames=[
                    "id",
                    "activity_type",
                    "resource_type",
                    "resource_id",
                    "action",
                    "status",
                    "title",
                    "description",
                    "created_at",
                ],
            )
            writer.writeheader()
for activity in activities:
                writer.writerow(
                    {
                        "id": activity.id,
                        "activity_type": activity.activity_type,
                        "resource_type": activity.resource_type,
                        "resource_id": activity.resource_id,
                        "action": activity.action,
                        "status": activity.status,
                        "title": activity.title,
                        "description": activity.description,
                        "created_at": activity.created_at.isoformat() if activity.created_at else None,
                    }
                )

            logger.info(f"Exported {len(activities)} activities as CSV for user {user_id}")

            return {
                "format": "csv",
                "count": len(activities),
                "data": output.getvalue(),
            }
else:  # json
            logger.info(f"Exported {len(activities)} activities as JSON for user {user_id}")

            return {
                "format": "json",
                "count": len(activities),
                "data": [a.to_dict() for a in activities],
            }

except HTTPException:
        raise
except Exception as e:
        logger.error(f"Error exporting activities for user {user_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to export activities")