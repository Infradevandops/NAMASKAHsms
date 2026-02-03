"""SMS Message model for inbox storage."""

from datetime import datetime
from sqlalchemy import Boolean, Column, DateTime, ForeignKey, String, Text
from app.models.base import Base


class SMSMessage(Base):
    """SMS message stored in inbox."""

    __tablename__ = "sms_messages"

    id = Column(String(36), primary_key=True, default=lambda: str(__import__("uuid").uuid4()))
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    rental_id = Column(String(36), ForeignKey("rentals.id"), nullable=True)
    from_number = Column(String(20), nullable=False)
    text = Column(Text, nullable=False)
    external_id = Column(String(100), unique=True, nullable=True)
    received_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    is_read = Column(Boolean, default=False, index=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
