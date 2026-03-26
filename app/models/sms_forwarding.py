"""SMS forwarding preferences model."""

from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, String

from app.models.base import BaseModel


class SMSForwarding(BaseModel):
    """
    Per-verification forwarding preferences.
    Telegram forwarding is reserved for future implementation.
    Use ForwardingConfig (forwarding_config table) for active forwarding configuration.
    """

    __tablename__ = "sms_forwarding"

    user_id = Column(String, ForeignKey("users.id"), nullable=False, index=True)

    # Forwarding destinations
    phone_number = Column(String(20), nullable=True)
    email = Column(String(255), nullable=True)
    telegram_id = Column(String(100), nullable=True)  # reserved — not yet active

    # Status flags
    phone_enabled = Column(Boolean, default=False)
    email_enabled = Column(Boolean, default=False)
    telegram_enabled = Column(Boolean, default=False)  # reserved — not yet active

    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(
        DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow
    )
