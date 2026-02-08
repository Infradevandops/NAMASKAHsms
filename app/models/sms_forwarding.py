"""SMS forwarding preferences model."""

from datetime import datetime

from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import Boolean, Column, DateTime, ForeignKey, String

from app.models.base import BaseModel


class SMSForwarding(BaseModel):
    """SMS forwarding configuration."""

    __tablename__ = "sms_forwarding"

    user_id = Column(UUID(as_uuid=False), ForeignKey("users.id"), nullable=False, index=True)
    rental_id = Column(UUID(as_uuid=False), ForeignKey("rentals.id"), nullable=True)

    # Forwarding destinations
    phone_number = Column(String(20), nullable=True)
    email = Column(String(255), nullable=True)
    telegram_id = Column(String(100), nullable=True)

    # Status flags
    phone_enabled = Column(Boolean, default=False)
    email_enabled = Column(Boolean, default=False)
    telegram_enabled = Column(Boolean, default=False)

    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)