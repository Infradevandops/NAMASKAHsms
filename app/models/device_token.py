"""Device token model for push notifications."""


from sqlalchemy import Boolean, Column, ForeignKey, String
from sqlalchemy.orm import relationship
from app.models.base import BaseModel

class DeviceToken(BaseModel):

    """Device token for push notifications."""

    __tablename__ = "device_tokens"

    user_id = Column(String, ForeignKey("users.id"), nullable=False, index=True)
    device_token = Column(String(500), nullable=False, unique=True, index=True)
    platform = Column(String(20), nullable=False)  # ios or android
    device_name = Column(String(255), nullable=True)  # e.g., "iPhone 14 Pro"
    is_active = Column(Boolean, default=True, index=True)

    # Relationship
    user = relationship("User", back_populates="device_tokens")

    def to_dict(self):

        """Convert to dictionary."""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "device_token": self.device_token,
            "platform": self.platform,
            "device_name": self.device_name,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
