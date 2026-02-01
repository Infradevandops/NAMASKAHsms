"""Notification preference model for user notification settings."""


from sqlalchemy import Boolean, Column, ForeignKey, String, Time
from sqlalchemy.orm import relationship
from app.models.base import BaseModel

class NotificationPreference(BaseModel):

    """User notification preferences for each notification type."""

    __tablename__ = "notification_preferences"

    user_id = Column(String, ForeignKey("users.id"), nullable=False, index=True)
    notification_type = Column(String(50), nullable=False)  # verification, payment, system, etc.
    enabled = Column(Boolean, default=True, nullable=False)  # Master toggle for this type
    delivery_methods = Column(String(255), default="toast")  # Comma-separated: toast,email,sms,webhook,push
    quiet_hours_start = Column(Time, nullable=True)  # Do not disturb start time (HH:MM)
    quiet_hours_end = Column(Time, nullable=True)  # Do not disturb end time (HH:MM)
    frequency = Column(String(20), default="instant")  # instant, daily, weekly, never
    created_at_override = Column(Boolean, default=False)  # Allow override of quiet hours
    push_enabled = Column(Boolean, default=True, nullable=False)  # Push notification toggle

    # Relationship
    user = relationship("User", back_populates="notification_preferences")

    def to_dict(self):

        """Convert to dictionary."""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "notification_type": self.notification_type,
            "enabled": self.enabled,
            "delivery_methods": self.delivery_methods.split(",") if self.delivery_methods else [],
            "quiet_hours_start": self.quiet_hours_start.isoformat() if self.quiet_hours_start else None,
            "quiet_hours_end": self.quiet_hours_end.isoformat() if self.quiet_hours_end else None,
            "frequency": self.frequency,
            "created_at_override": self.created_at_override,
            "push_enabled": self.push_enabled,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class NotificationPreferenceDefaults(BaseModel):

        """Default notification preferences for new users."""

        __tablename__ = "notification_preference_defaults"

        notification_type = Column(String(50), nullable=False, unique=True, index=True)
        enabled = Column(Boolean, default=True, nullable=False)
        delivery_methods = Column(String(255), default="toast")
        frequency = Column(String(20), default="instant")
        description = Column(String(255), nullable=True)

    def to_dict(self):

        """Convert to dictionary."""
        return {
            "id": self.id,
            "notification_type": self.notification_type,
            "enabled": self.enabled,
            "delivery_methods": self.delivery_methods.split(",") if self.delivery_methods else [],
            "frequency": self.frequency,
            "description": self.description,
        }
