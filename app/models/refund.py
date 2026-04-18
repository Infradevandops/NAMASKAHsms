"""Refund model for payment refunds."""

from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, Float, ForeignKey, String

from app.models.base import BaseModel


class Refund(BaseModel):
    """Refund record model."""

    __tablename__ = "refunds"

    payment_id = Column(
        String, ForeignKey("payment_logs.id"), nullable=False, index=True
    )
    user_id = Column(String, ForeignKey("users.id"), nullable=False, index=True)
    amount = Column(Float, nullable=False)
    reason = Column(String, nullable=False)
    status = Column(
        String, nullable=False, index=True
    )  # pending, success, failed, cancelled
    reference = Column(String, unique=True, index=True, nullable=False)
    initiated_by = Column(String)  # admin or system
    initiated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    processed_at = Column(DateTime)
    error_message = Column(String)

    # Retry tracking for failed refunds
    failed_attempts = Column(
        String, nullable=False, index=True, default="0"
    )  # Comma-separated attempt dates
    max_retry_attempts = Column(String, default="3")
    next_retry_at = Column(DateTime)

    created_at = Column(
        DateTime, default=lambda: datetime.now(timezone.utc), nullable=False, index=True
    )
    updated_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )
