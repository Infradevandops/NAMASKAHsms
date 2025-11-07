"""Rental model for SMS number rentals."""
from sqlalchemy import Column, DateTime, Integer, Numeric, String
from sqlalchemy.sql import func

from app.models.base import BaseModel


class Rental(BaseModel):
    __tablename__ = "rentals"

    user_id = Column(String(36), nullable=False, index=True)
    phone_number = Column(String(20), nullable=False)
    service_name = Column(String(50), nullable=False)
    country_code = Column(String(3), nullable=False)
    provider = Column(String(20), default="5sim")
    activation_id = Column(String(50), nullable=False)
    expires_at = Column(DateTime, nullable=False)
    status = Column(String(20), default="active")
    cost = Column(Numeric(10, 4), nullable=False)
    duration_hours = Column(Integer, default=24)

    @property
    def time_remaining_seconds(self) -> int:
        """Calculate remaining time in seconds."""
        if self.expires_at:
            remaining = (self.expires_at - func.now()).total_seconds()
            return max(0, int(remaining))
        return 0

    @property
    def is_expired(self) -> bool:
        """Check if rental is expired."""
        return self.time_remaining_seconds <= 0
