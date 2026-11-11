"""Stock watch model — user watches an out-of-stock service for back-in-stock notification."""

import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, ForeignKey, String, UniqueConstraint

from app.models.base import BaseModel


class StockWatch(BaseModel):
    __tablename__ = "stock_watches"

    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    service_name = Column(String(100), nullable=False, index=True)
    capability = Column(String(20), nullable=False, default="sms")
    created_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    notified_at = Column(DateTime, nullable=True)

    __table_args__ = (
        UniqueConstraint("user_id", "service_name", "capability", name="uq_stock_watch"),
    )
