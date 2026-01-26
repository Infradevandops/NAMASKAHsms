"""Activity service for tracking user events."""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.core.logging import get_logger
from app.models.activity import Activity
from app.models.user import User

logger = get_logger(__name__)


class ActivityService:
    """Service for managing user activities."""

    def __init__(self, db: Session):
        """Initialize activity service with database session."""
        self.db = db

    def log_activity(
        self,
        user_id: str,
        activity_type: str,
        resource_type: str,
        action: str,
        title: str,
        description: Optional[str] = None,
        resource_id: Optional[str] = None,
        status: str = "completed",
        metadata: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> Activity:
        """Log a user activity.

        Args:
            user_id: User ID
            activity_type: Type of activity (verification, payment, login, settings, api_key)
            resource_type: Type of resource (verification, payment, user, api_key)
            action: Action performed (created, completed, failed, updated, deleted)
            title: Activity title
            description: Activity description
            resource_id: ID of the resource
            status: Activity status (completed, pending, failed)
            metadata: Additional context data
            ip_address: IP address of the request
            user_agent: User agent string

        Returns:
            Created activity

        Raises:
            ValueError: If user not found
        """
        # Verify user exists
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            raise ValueError(f"User {user_id} not found")

        # Create activity
        activity = Activity(
            user_id=user_id,
            activity_type=activity_type,
            resource_type=resource_type,
            resource_id=resource_id,
            action=action,
            status=status,
            title=title,
            description=description,
            metadata=metadata,
            ip_address=ip_address,
            user_agent=user_agent,
        )

        self.db.add(activity)
        self.db.commit()

        logger.info(
            f"Activity logged: User={user_id}, Type={activity_type}, "
            f"Action={action}, Status={status}, Title={title}"
        )

        return activity

    def get_user_activities(
        self,
        user_id: str,
        activity_type: Optional[str] = None,
        resource_type: Optional[str] = None,
        status: Optional[str] = None,
        skip: int = 0,
        limit: int = 20,
    ) -> Dict[str, Any]:
        """Get activities for user with filtering.

        Args:
            user_id: User ID
            activity_type: Filter by activity type
            resource_type: Filter by resource type
            status: Filter by status
            skip: Number of records to skip
            limit: Number of records to return

        Returns:
            Dictionary with activities and metadata

        Raises:
            ValueError: If user not found
        """
        # Verify user exists
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            raise ValueError(f"User {user_id} not found")

        # Build query
        query = self.db.query(Activity).filter(Activity.user_id == user_id)

        # Apply filters
        if activity_type:
            query = query.filter(Activity.activity_type == activity_type)

        if resource_type:
            query = query.filter(Activity.resource_type == resource_type)

        if status:
            query = query.filter(Activity.status == status)

        # Get total count
        total = query.count()

        # Order by newest first and apply pagination
        activities = query.order_by(desc(Activity.created_at)).offset(skip).limit(limit).all()

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

    def get_activity_by_id(self, user_id: str, activity_id: str) -> Optional[Activity]:
        """Get activity by ID for user.

        Args:
            user_id: User ID
            activity_id: Activity ID

        Returns:
            Activity or None if not found

        Raises:
            ValueError: If user not found
        """
        # Verify user exists
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            raise ValueError(f"User {user_id} not found")

        activity = self.db.query(Activity).filter(Activity.id == activity_id, Activity.user_id == user_id).first()

        if activity:
            logger.info(f"Retrieved activity {activity_id} for user {user_id}")
        else:
            logger.warning(f"Activity {activity_id} not found for user {user_id}")

        return activity

    def get_activities_by_resource(self, user_id: str, resource_type: str, resource_id: str) -> List[Activity]:
        """Get all activities for a specific resource.

        Args:
            user_id: User ID
            resource_type: Type of resource
            resource_id: ID of resource

        Returns:
            List of activities

        Raises:
            ValueError: If user not found
        """
        # Verify user exists
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            raise ValueError(f"User {user_id} not found")

        activities = (
            self.db.query(Activity)
            .filter(
                Activity.user_id == user_id,
                Activity.resource_type == resource_type,
                Activity.resource_id == resource_id,
            )
            .order_by(desc(Activity.created_at))
            .all()
        )

        logger.info(
            f"Retrieved {len(activities)} activities for resource {resource_type}/{resource_id} " f"for user {user_id}"
        )

        return activities

    def get_activity_summary(self, user_id: str, days: int = 30) -> Dict[str, Any]:
        """Get activity summary for user.

        Args:
            user_id: User ID
            days: Number of days to include

        Returns:
            Dictionary with activity summary

        Raises:
            ValueError: If user not found
        """
        # Verify user exists
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            raise ValueError(f"User {user_id} not found")

        # Calculate date threshold
        from datetime import timedelta

        threshold = datetime.now(timezone.utc) - timedelta(days=days)

        # Get activities within timeframe
        activities = self.db.query(Activity).filter(Activity.user_id == user_id, Activity.created_at >= threshold).all()

        # Build summary
        summary = {
            "total_activities": len(activities),
            "by_type": {},
            "by_status": {},
            "by_resource": {},
        }

        for activity in activities:
            # Count by type
            summary["by_type"][activity.activity_type] = summary["by_type"].get(activity.activity_type, 0) + 1

            # Count by status
            summary["by_status"][activity.status] = summary["by_status"].get(activity.status, 0) + 1

            # Count by resource
            summary["by_resource"][activity.resource_type] = summary["by_resource"].get(activity.resource_type, 0) + 1

        logger.info(f"Generated activity summary for user {user_id} (last {days} days)")

        return summary

    def cleanup_old_activities(self, days: int = 90) -> int:
        """Delete activities older than specified days.

        Args:
            days: Number of days to keep

        Returns:
            Number of activities deleted
        """
        from datetime import timedelta

        threshold = datetime.now(timezone.utc) - timedelta(days=days)

        deleted_count = self.db.query(Activity).filter(Activity.created_at < threshold).delete()

        self.db.commit()

        logger.info(f"Cleaned up {deleted_count} activities older than {days} days")

        return deleted_count
