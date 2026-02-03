"""Notification analytics model for tracking delivery and engagement metrics."""

from sqlalchemy import JSON, Column, ForeignKey, Integer, String

from app.models.base import BaseModel


class NotificationAnalytics(BaseModel):
    """Notification delivery and engagement analytics."""

    __tablename__ = "notification_analytics"

    notification_id = Column(String, ForeignKey("notifications.id"), nullable=False, index=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=False, index=True)
    notification_type = Column(String(50), nullable=False, index=True)
    delivery_method = Column(String(50), nullable=False)  # email, sms, toast, webhook, websocket
    status = Column(String(20), default="sent", nullable=False, index=True)  # sent, delivered, read, clicked, failed
    sent_at = Column(String, nullable=True)
    delivered_at = Column(String, nullable=True)
    read_at = Column(String, nullable=True)
    clicked_at = Column(String, nullable=True)
    failed_at = Column(String, nullable=True)
    failure_reason = Column(String(255), nullable=True)
    delivery_time_ms = Column(Integer, nullable=True)  # Time from sent to delivered in milliseconds
    read_time_ms = Column(Integer, nullable=True)  # Time from delivered to read in milliseconds
    click_time_ms = Column(Integer, nullable=True)  # Time from delivered to clicked in milliseconds
    retry_count = Column(Integer, default=0, nullable=False)
    tracking_data = Column(JSON, nullable=True)  # Additional tracking data

    def to_dict(self):
        """Convert to dictionary."""
        return {
            "id": self.id,
            "notification_id": self.notification_id,
            "user_id": self.user_id,
            "notification_type": self.notification_type,
            "delivery_method": self.delivery_method,
            "status": self.status,
            "sent_at": self.sent_at,
            "delivered_at": self.delivered_at,
            "read_at": self.read_at,
            "clicked_at": self.clicked_at,
            "failed_at": self.failed_at,
            "failure_reason": self.failure_reason,
            "delivery_time_ms": self.delivery_time_ms,
            "read_time_ms": self.read_time_ms,
            "click_time_ms": self.click_time_ms,
            "retry_count": self.retry_count,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
