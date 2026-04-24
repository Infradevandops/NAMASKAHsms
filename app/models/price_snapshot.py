"""Price snapshot model for historical cost tracking."""

from sqlalchemy import DECIMAL, Column, DateTime, String
from sqlalchemy.sql import func

from app.models.base import BaseModel


class PriceSnapshot(BaseModel):
    """
    Model for recording a snapshot of provider prices at a specific point in time.
    Used for historical analytics and trend detection.
    """

    __tablename__ = "price_snapshots"

    service_id = Column(String(100), nullable=False, index=True)
    service_name = Column(String(255), nullable=False)
    provider_cost = Column(DECIMAL(10, 4), nullable=False)
    platform_price = Column(DECIMAL(10, 4), nullable=False)
    markup_percentage = Column(DECIMAL(5, 2), nullable=False)
    currency = Column(String(3), default="USD")
    captured_at = Column(DateTime, server_default=func.now(), index=True)
    source = Column(String(50), default="textverified")

    def __repr__(self):
        return (
            f"<PriceSnapshot(service='{self.service_id}', cost={self.provider_cost})>"
        )
