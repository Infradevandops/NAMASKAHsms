"""SMS forwarding preferences model."""

from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, String

from app.models.base import Base


class SMSForwarding(Base):
    """SMS forwarding configuration."""

    __tablename__ = "sms_forwarding"

    id = Column(String(36), primary_key=True, default=lambda: str(__import__("uuid").uuid4()))
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    rental_id = Column(String(36), ForeignKey("rentals.id"), nullable=True)

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