"""Notification analytics service for tracking delivery and engagement metrics."""

from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

from sqlalchemy import and_
from sqlalchemy.orm import Session

from app.core.logging import get_logger
from app.models.notification_analytics import NotificationAnalytics

logger = get_logger(__name__)


class NotificationAnalyticsService:
    """Service for tracking and analyzing notification metrics."""

    def __init__(self, db: Session):
        """Initialize notification analytics service.

        Args:
            db: Database session
        """
        self.db = db

    def track_notification_sent(
        self,
        notification_id: str,
        user_id: str,
        notification_type: str,
        delivery_method: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> NotificationAnalytics:
        """Track notification sent event.

        Args:
            notification_id: Notification ID
            user_id: User ID
            notification_type: Type of notification
            delivery_method: Delivery method (email, sms, toast, webhook, websocket)
            metadata: Additional metadata

        Returns:
            NotificationAnalytics record
        """
        try:
            analytics = NotificationAnalytics(
                notification_id=notification_id,
                user_id=user_id,
                notification_type=notification_type,
                delivery_method=delivery_method,
                status="sent",
                sent_at=datetime.now(timezone.utc).isoformat(),
                metadata=metadata,
            )

            self.db.add(analytics)
            self.db.commit()

            logger.info(
                f"Notification sent tracked: notification_id={notification_id}, "
                f"user_id={user_id}, method={delivery_method}"
            )

            return analytics

        except Exception as e:
            logger.error(f"Failed to track notification sent: {e}")
            raise

    def track_notification_delivered(
        self,
        notification_id: str,
        user_id: str,
        delivery_method: str,
    ) -> bool:
        """Track notification delivered event.

        Args:
            notification_id: Notification ID
            user_id: User ID
            delivery_method: Delivery method

        Returns:
            True if tracking successful, False otherwise
        """
        try:
            analytics = (
                self.db.query(NotificationAnalytics)
                .filter(
                    and_(
                        NotificationAnalytics.notification_id == notification_id,
                        NotificationAnalytics.user_id == user_id,
                        NotificationAnalytics.delivery_method == delivery_method,
                    )
                )
                .first()
            )

            if not analytics:
                logger.warning(
                    f"Analytics record not found for notification {notification_id}, "
                    f"user {user_id}, method {delivery_method}"
                )
                return False

            now = datetime.now(timezone.utc)
            analytics.status = "delivered"
            analytics.delivered_at = now.isoformat()

            # Calculate delivery time
            if analytics.sent_at:
                sent_time = datetime.fromisoformat(analytics.sent_at)
                analytics.delivery_time_ms = int((now - sent_time).total_seconds() * 1000)

            self.db.commit()

            logger.info(
                f"Notification delivered tracked: notification_id={notification_id}, "
                f"delivery_time_ms={analytics.delivery_time_ms}"
            )

            return True

        except Exception as e:
            logger.error(f"Failed to track notification delivered: {e}")
            return False

    def track_notification_read(
        self,
        notification_id: str,
        user_id: str,
    ) -> bool:
        """Track notification read event.

        Args:
            notification_id: Notification ID
            user_id: User ID

        Returns:
            True if tracking successful, False otherwise
        """
        try:
            analytics = (
                self.db.query(NotificationAnalytics)
                .filter(
                    and_(
                        NotificationAnalytics.notification_id == notification_id,
                        NotificationAnalytics.user_id == user_id,
                    )
                )
                .first()
            )

            if not analytics:
                logger.warning(f"Analytics record not found for notification {notification_id}")
                return False

            now = datetime.now(timezone.utc)
            analytics.status = "read"
            analytics.read_at = now.isoformat()

            # Calculate read time
            if analytics.delivered_at:
                delivered_time = datetime.fromisoformat(analytics.delivered_at)
                analytics.read_time_ms = int((now - delivered_time).total_seconds() * 1000)

            self.db.commit()

            logger.info(
                f"Notification read tracked: notification_id={notification_id}, "
                f"read_time_ms={analytics.read_time_ms}"
            )

            return True

        except Exception as e:
            logger.error(f"Failed to track notification read: {e}")
            return False

    def track_notification_clicked(
        self,
        notification_id: str,
        user_id: str,
    ) -> bool:
        """Track notification clicked event.

        Args:
            notification_id: Notification ID
            user_id: User ID

        Returns:
            True if tracking successful, False otherwise
        """
        try:
            analytics = (
                self.db.query(NotificationAnalytics)
                .filter(
                    and_(
                        NotificationAnalytics.notification_id == notification_id,
                        NotificationAnalytics.user_id == user_id,
                    )
                )
                .first()
            )

            if not analytics:
                logger.warning(f"Analytics record not found for notification {notification_id}")
                return False

            now = datetime.now(timezone.utc)
            analytics.status = "clicked"
            analytics.clicked_at = now.isoformat()

            # Calculate click time
            if analytics.delivered_at:
                delivered_time = datetime.fromisoformat(analytics.delivered_at)
                analytics.click_time_ms = int((now - delivered_time).total_seconds() * 1000)

            self.db.commit()

            logger.info(
                f"Notification clicked tracked: notification_id={notification_id}, "
                f"click_time_ms={analytics.click_time_ms}"
            )

            return True

        except Exception as e:
            logger.error(f"Failed to track notification clicked: {e}")
            return False

    def track_notification_failed(
        self,
        notification_id: str,
        user_id: str,
        delivery_method: str,
        reason: str,
    ) -> bool:
        """Track notification failed event.

        Args:
            notification_id: Notification ID
            user_id: User ID
            delivery_method: Delivery method
            reason: Failure reason

        Returns:
            True if tracking successful, False otherwise
        """
        try:
            analytics = (
                self.db.query(NotificationAnalytics)
                .filter(
                    and_(
                        NotificationAnalytics.notification_id == notification_id,
                        NotificationAnalytics.user_id == user_id,
                        NotificationAnalytics.delivery_method == delivery_method,
                    )
                )
                .first()
            )

            if not analytics:
                logger.warning(f"Analytics record not found for notification {notification_id}")
                return False

            analytics.status = "failed"
            analytics.failed_at = datetime.now(timezone.utc).isoformat()
            analytics.failure_reason = reason
            analytics.retry_count += 1

            self.db.commit()

            logger.info(
                f"Notification failed tracked: notification_id={notification_id}, "
                f"reason={reason}, retry_count={analytics.retry_count}"
            )

            return True

        except Exception as e:
            logger.error(f"Failed to track notification failed: {e}")
            return False

    def get_delivery_metrics(
        self,
        user_id: Optional[str] = None,
        notification_type: Optional[str] = None,
        days: int = 30,
    ) -> Dict[str, Any]:
        """Get notification delivery metrics.

        Args:
            user_id: Filter by user ID (optional)
            notification_type: Filter by notification type (optional)
            days: Number of days to include

        Returns:
            Dictionary with delivery metrics
        """
        try:
            threshold = datetime.now(timezone.utc) - timedelta(days=days)

            query = self.db.query(NotificationAnalytics).filter(NotificationAnalytics.created_at >= threshold)

            if user_id:
                query = query.filter(NotificationAnalytics.user_id == user_id)

            if notification_type:
                query = query.filter(NotificationAnalytics.notification_type == notification_type)

            analytics = query.all()

            # Calculate metrics
            total = len(analytics)
            sent = len([a for a in analytics if a.status in ["sent", "delivered", "read", "clicked"]])
            delivered = len([a for a in analytics if a.status in ["delivered", "read", "clicked"]])
            read = len([a for a in analytics if a.status in ["read", "clicked"]])
            clicked = len([a for a in analytics if a.status == "clicked"])
            failed = len([a for a in analytics if a.status == "failed"])

            # Calculate rates
            delivery_rate = (delivered / sent * 100) if sent > 0 else 0
            read_rate = (read / delivered * 100) if delivered > 0 else 0
            click_rate = (clicked / delivered * 100) if delivered > 0 else 0
            failure_rate = (failed / total * 100) if total > 0 else 0

            # Calculate average times
            delivery_times = [a.delivery_time_ms for a in analytics if a.delivery_time_ms]
            read_times = [a.read_time_ms for a in analytics if a.read_time_ms]
            click_times = [a.click_time_ms for a in analytics if a.click_time_ms]

            avg_delivery_time = sum(delivery_times) / len(delivery_times) if delivery_times else 0
            avg_read_time = sum(read_times) / len(read_times) if read_times else 0
            avg_click_time = sum(click_times) / len(click_times) if click_times else 0

            logger.info(
                f"Delivery metrics calculated: total={total}, delivery_rate={delivery_rate:.2f}%, "
                f"read_rate={read_rate:.2f}%, click_rate={click_rate:.2f}%"
            )

            return {
                "total_notifications": total,
                "sent": sent,
                "delivered": delivered,
                "read": read,
                "clicked": clicked,
                "failed": failed,
                "delivery_rate": round(delivery_rate, 2),
                "read_rate": round(read_rate, 2),
                "click_rate": round(click_rate, 2),
                "failure_rate": round(failure_rate, 2),
                "avg_delivery_time_ms": round(avg_delivery_time, 2),
                "avg_read_time_ms": round(avg_read_time, 2),
                "avg_click_time_ms": round(avg_click_time, 2),
            }

        except Exception as e:
            logger.error(f"Failed to get delivery metrics: {e}")
            return {}

    def get_metrics_by_type(
        self,
        user_id: Optional[str] = None,
        days: int = 30,
    ) -> Dict[str, Dict[str, Any]]:
        """Get metrics grouped by notification type.

        Args:
            user_id: Filter by user ID (optional)
            days: Number of days to include

        Returns:
            Dictionary with metrics by type
        """
        try:
            threshold = datetime.now(timezone.utc) - timedelta(days=days)

            query = self.db.query(NotificationAnalytics).filter(NotificationAnalytics.created_at >= threshold)

            if user_id:
                query = query.filter(NotificationAnalytics.user_id == user_id)

            analytics = query.all()

            # Group by type
            by_type = {}
            for a in analytics:
                if a.notification_type not in by_type:
                    by_type[a.notification_type] = []
                by_type[a.notification_type].append(a)

            # Calculate metrics for each type
            result = {}
            for notification_type, records in by_type.items():
                total = len(records)
                delivered = len([r for r in records if r.status in ["delivered", "read", "clicked"]])
                read = len([r for r in records if r.status in ["read", "clicked"]])
                clicked = len([r for r in records if r.status == "clicked"])
                failed = len([r for r in records if r.status == "failed"])

                result[notification_type] = {
                    "total": total,
                    "delivered": delivered,
                    "read": read,
                    "clicked": clicked,
                    "failed": failed,
                    "delivery_rate": round((delivered / total * 100) if total > 0 else 0, 2),
                    "read_rate": round((read / delivered * 100) if delivered > 0 else 0, 2),
                    "click_rate": round((clicked / delivered * 100) if delivered > 0 else 0, 2),
                }

            logger.info(f"Metrics by type calculated: {len(result)} types")

            return result

        except Exception as e:
            logger.error(f"Failed to get metrics by type: {e}")
            return {}

    def get_metrics_by_method(
        self,
        user_id: Optional[str] = None,
        days: int = 30,
    ) -> Dict[str, Dict[str, Any]]:
        """Get metrics grouped by delivery method.

        Args:
            user_id: Filter by user ID (optional)
            days: Number of days to include

        Returns:
            Dictionary with metrics by method
        """
        try:
            threshold = datetime.now(timezone.utc) - timedelta(days=days)

            query = self.db.query(NotificationAnalytics).filter(NotificationAnalytics.created_at >= threshold)

            if user_id:
                query = query.filter(NotificationAnalytics.user_id == user_id)

            analytics = query.all()

            # Group by method
            by_method = {}
            for a in analytics:
                if a.delivery_method not in by_method:
                    by_method[a.delivery_method] = []
                by_method[a.delivery_method].append(a)

            # Calculate metrics for each method
            result = {}
            for method, records in by_method.items():
                total = len(records)
                delivered = len([r for r in records if r.status in ["delivered", "read", "clicked"]])
                read = len([r for r in records if r.status in ["read", "clicked"]])
                clicked = len([r for r in records if r.status == "clicked"])
                failed = len([r for r in records if r.status == "failed"])

                result[method] = {
                    "total": total,
                    "delivered": delivered,
                    "read": read,
                    "clicked": clicked,
                    "failed": failed,
                    "delivery_rate": round((delivered / total * 100) if total > 0 else 0, 2),
                    "read_rate": round((read / delivered * 100) if delivered > 0 else 0, 2),
                    "click_rate": round((clicked / delivered * 100) if delivered > 0 else 0, 2),
                }

            logger.info(f"Metrics by method calculated: {len(result)} methods")

            return result

        except Exception as e:
            logger.error(f"Failed to get metrics by method: {e}")
            return {}

    def get_timeline_metrics(
        self,
        user_id: Optional[str] = None,
        days: int = 30,
        interval: str = "day",
    ) -> List[Dict[str, Any]]:
        """Get metrics over time.

        Args:
            user_id: Filter by user ID (optional)
            days: Number of days to include
            interval: Time interval (day, hour)

        Returns:
            List of metrics by time period
        """
        try:
            threshold = datetime.now(timezone.utc) - timedelta(days=days)

            query = self.db.query(NotificationAnalytics).filter(NotificationAnalytics.created_at >= threshold)

            if user_id:
                query = query.filter(NotificationAnalytics.user_id == user_id)

            analytics = query.all()

            # Group by time period
            by_period = {}
            for a in analytics:
                if interval == "day":
                    period = a.created_at.date().isoformat()
                else:  # hour
                    period = a.created_at.replace(minute=0, second=0, microsecond=0).isoformat()

                if period not in by_period:
                    by_period[period] = []
                by_period[period].append(a)

            # Calculate metrics for each period
            result = []
            for period in sorted(by_period.keys()):
                records = by_period[period]
                total = len(records)
                delivered = len([r for r in records if r.status in ["delivered", "read", "clicked"]])
                read = len([r for r in records if r.status in ["read", "clicked"]])
                clicked = len([r for r in records if r.status == "clicked"])
                failed = len([r for r in records if r.status == "failed"])

                result.append(
                    {
                        "period": period,
                        "total": total,
                        "delivered": delivered,
                        "read": read,
                        "clicked": clicked,
                        "failed": failed,
                        "delivery_rate": round((delivered / total * 100) if total > 0 else 0, 2),
                        "read_rate": round((read / delivered * 100) if delivered > 0 else 0, 2),
                        "click_rate": round((clicked / delivered * 100) if delivered > 0 else 0, 2),
                    }
                )

            logger.info(f"Timeline metrics calculated: {len(result)} periods")

            return result

        except Exception as e:
            logger.error(f"Failed to get timeline metrics: {e}")
            return []
