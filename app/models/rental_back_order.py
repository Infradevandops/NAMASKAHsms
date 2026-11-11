"""Rental back-order model — TV back-order queued when no rental inventory available."""

from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, ForeignKey, Numeric, String

from app.models.base import BaseModel


class RentalBackOrder(BaseModel):
    __tablename__ = "rental_back_orders"

    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    tv_back_order_id = Column(String(100), nullable=False, unique=True)
    service_name = Column(String(100), nullable=False)
    capability = Column(String(20), nullable=False, default="sms")
    requested_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    fulfilled_at = Column(DateTime, nullable=True)
    notified_at = Column(DateTime, nullable=True)
    credits_held = Column(Numeric(10, 4), nullable=False)
