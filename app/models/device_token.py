"""Device token model for push notifications."""

from datetime import datetime, timedelta

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from app.models.base import BaseModel


class DeviceToken(BaseModel):
    """Device token for push notifications."""

    __tablename__ = "device_tokens"

    user_id = Column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    token = Column(String(500), nullable=False, unique=True, index=True)
    platform = Column(String(20), nullable=False)  # ios, android, or web
    device_type = Column(
        String(50), nullable=True
    )  # browser name for web, device model for mobile
    device_name = Column(String(255), nullable=True)  # user-friendly name
    active = Column(Boolean, default=True, nullable=False, index=True)
    last_used_at = Column(DateTime, nullable=True)
    expires_at = Column(DateTime, nullable=True)

    # Relationship
    user = relationship("User", back_populates="device_tokens")

    def is_expired(self) -> bool:
        """Check if token is expired."""
        if not self.expires_at:
            return False
        return datetime.utcnow() > self.expires_at

    def refresh_expiry(self, days: int = 90):
        """Refresh token expiry date."""
        self.expires_at = datetime.utcnow() + timedelta(days=days)
        self.last_used_at = datetime.utcnow()

    def to_dict(self):
        """Convert to dictionary."""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "token": self.token,
            "platform": self.platform,
            "device_type": self.device_type,
            "device_name": self.device_name,
            "active": self.active,
            "last_used_at": (
                self.last_used_at.isoformat() if self.last_used_at else None
            ),
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
