"""Activity tracking API endpoints."""

from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.dependencies import get_current_user_id
from app.core.logging import get_logger
from app.models.activity import Activity
from app.models.user import User
from app.schemas.activity import ActivityResponse

logger = get_logger(__name__)
router = APIRouter(prefix="/api/activities", tags=["Activities"])


@router.get("/", response_model=List[ActivityResponse])
async def get_user_activities(
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    resource_type: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    date_from: Optional[str] = Query(None),
    date_to: Optional[str] = Query(None),
):
    """Get user activities with filtering and pagination.
    
    Returns:
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
                date_to_obj = datetime.strptime(date_to, "%Y-%m-%d")
                query = query.filter(Activity.created_at <= date_to_obj)
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid date_to format (use YYYY-MM-DD)")

        # Apply pagination and ordering
        activities = (
            query.order_by(Activity.created_at.desc())
            .offset(offset)
            .limit(limit)
            .all()
        )

        logger.info(f"Retrieved {len(activities)} activities for user {user_id}")

        return [
            ActivityResponse(
                id=activity.id,
                resource_type=activity.resource_type,
                resource_id=activity.resource_id,
                action=activity.action,
                status=activity.status,
                details=activity.details or {},
                created_at=activity.created_at,
            )
            for activity in activities
        ]

    except Exception as e:
        logger.error(f"Failed to retrieve activities for user {user_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve activities")


@router.get("/summary")
async def get_activity_summary(
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Get activity summary for user."""
    try:
        # Get activity counts by type
        activities = db.query(Activity).filter(Activity.user_id == user_id).all()
        
        summary = {
            "total_activities": len(activities),
            "by_resource_type": {},
            "by_status": {},
            "recent_count": 0
        }

        # Count by resource type and status
        for activity in activities:
            # By resource type
            resource_type = activity.resource_type or "unknown"
            summary["by_resource_type"][resource_type] = summary["by_resource_type"].get(resource_type, 0) + 1
            
            # By status
            status = activity.status or "unknown"
            summary["by_status"][status] = summary["by_status"].get(status, 0) + 1
            
            # Recent activities (last 24 hours)
            if activity.created_at and (datetime.utcnow() - activity.created_at).days < 1:
                summary["recent_count"] += 1

        return summary

    except Exception as e:
        logger.error(f"Failed to get activity summary for user {user_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get activity summary")