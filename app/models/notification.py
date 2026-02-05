"""Notification model for user notifications."""

from sqlalchemy import Boolean, Column, ForeignKey, String, Text
from sqlalchemy.orm import relationship

from app.models.base import BaseModel


class Notification(BaseModel):
    """User notification model."""

    __tablename__ = "notifications"

    user_id = Column(String, ForeignKey("users.id"), nullable=False, index=True)
    type = Column(String(50), nullable=False)  # sms_received, credit_added, etc
    title = Column(String(255), nullable=False)
    message = Column(Text)
    link = Column(String(255))
    icon = Column(String(50))
    is_read = Column(Boolean, default=False, index=True)

    # Relationship
    user = relationship("User", back_populates="notifications")

    def to_dict(self):
        """Convert to dictionary."""
        return {
            "id": self.id,
            "type": self.type,
            "title": self.title,
            "message": self.message,
            "link": self.link,
            "icon": self.icon,
            "is_read": self.is_read,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }