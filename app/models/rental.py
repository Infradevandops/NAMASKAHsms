"""Rental model for number rentals."""

import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, Float, String, Uuid

from app.models.base import Base


class Rental(Base):
    """Number rental model."""

    __tablename__ = "rentals"

    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(Uuid(as_uuid=True), nullable=False, index=True)
    phone_number = Column(String(20), nullable=False)
    cost = Column(Float, nullable=False, default=0.0)
    status = Column(String(50), nullable=False, default="active")
    created_at = Column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    updated_at = Column(
        DateTime(timezone=True), onupdate=lambda: datetime.now(timezone.utc)
    )
