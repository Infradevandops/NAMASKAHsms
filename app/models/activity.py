"""Activity model for tracking user events."""

from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import JSON, Column, ForeignKey, String, Text
from sqlalchemy.orm import relationship

from app.models.base import BaseModel


class Activity(BaseModel):
    """User activity tracking model."""

    __tablename__ = "activities"

    user_id = Column(UUID(as_uuid=False), ForeignKey("users.id"), nullable=False, index=True)
    activity_type = Column(String(50), nullable=False, index=True)  # verification, payment, login, settings, api_key
    resource_type = Column(String(50), nullable=False)  # verification, payment, user, api_key
    resource_id = Column(String(255), nullable=True, index=True)
    action = Column(String(100), nullable=False)  # created, completed, failed, updated, deleted
    status = Column(String(20), default="completed", nullable=False)  # completed, pending, failed
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    activity_data = Column(JSON, nullable=True)  # Additional context (cost, service_name, etc.)
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(Text, nullable=True)

    # Relationship - disabled to fix circular import
    # user = relationship("User", back_populates="activities")

    def to_dict(self):
        """Convert to dictionary."""
        return {
            "id": self.id,
            "activity_type": self.activity_type,
            "resource_type": self.resource_type,
            "resource_id": self.resource_id,
            "action": self.action,
            "status": self.status,
            "title": self.title,
            "description": self.description,
            "activity_data": self.activity_data,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }