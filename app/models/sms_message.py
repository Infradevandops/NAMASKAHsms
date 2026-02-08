"""SMS Message model for inbox storage."""

from datetime import datetime

from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import Boolean, Column, DateTime, ForeignKey, String, Text

from app.models.base import BaseModel


class SMSMessage(BaseModel):
    """SMS message stored in inbox."""

    __tablename__ = "sms_messages"

    user_id = Column(UUID(as_uuid=False), ForeignKey("users.id"), nullable=False, index=True)
    rental_id = Column(UUID(as_uuid=False), ForeignKey("rentals.id"), nullable=True)
    from_number = Column(String(20), nullable=False)
    text = Column(Text, nullable=False)
    external_id = Column(String(100), unique=True, nullable=True)
    received_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    is_read = Column(Boolean, default=False, index=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)