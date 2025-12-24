"""Notification model for in-app notifications."""
from sqlalchemy import Boolean, Column, String, JSON, DateTime
from datetime import datetime, timezone

from app.models.base import BaseModel


class Notification(BaseModel):
    """In-app notification model."""

    __tablename__ = "notifications"

    user_id = Column(String, nullable=False, index=True)
    type = Column(String, nullable=True, index=True)  # payment_success, payment_failed, refund_success, info
    title = Column(String, nullable=False)
    message = Column(String, nullable=False)
    data = Column(JSON)  # Additional data (reference, amount, etc)
    read = Column(Boolean, default=False, nullable=False, index=True)
    read_at = Column(DateTime)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False, index=True)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
