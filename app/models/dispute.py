"""Dispute and chargeback models for payment disputes."""

from datetime import datetime, timezone

from sqlalchemy import Boolean, Column, DateTime, Float, ForeignKey, String

from app.models.base import BaseModel


class Dispute(BaseModel):
    """Payment dispute/chargeback model for tracking disputes."""

    __tablename__ = "disputes"

    user_id = Column(String, ForeignKey("users.id"), nullable=False, index=True)
    transaction_id = Column(
        String, ForeignKey("sms_transactions.id"), nullable=True, index=True
    )
    payment_log_id = Column(
        String, ForeignKey("payment_logs.id"), nullable=False, index=True
    )

    # Dispute details
    amount = Column(Float, nullable=False)
    reason_code = Column(String, nullable=False, index=True)  # Chargeback reason
    reason_description = Column(String, nullable=False)
    dispute_date = Column(DateTime, nullable=False, index=True)

    # Status tracking
    status = Column(
        String,
        default="opened",
        nullable=False,
        index=True,
    )  # opened, under_review, won, lost, appealed

    # Resolution
    resolution = Column(String)  # won, lost, appealed
    resolution_date = Column(DateTime)
    resolution_notes = Column(String)

    # Impact on user
    balance_reversed = Column(Boolean, default=False)
    reversal_amount = Column(Float, nullable=True)
    reversal_at = Column(DateTime, nullable=True)

    # Evidence
    evidence_notes = Column(String)
    evidence_files = Column(String)  # JSON of file URLs

    # Admin tracking
    assigned_to = Column(String)  # Admin user_id
    assigned_at = Column(DateTime)
    last_updated_by = Column(String)
    last_updated_at = Column(DateTime)

    # Timing
    created_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
        index=True,
    )
    updated_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Reason codes reference
    CHARGEBACK_REASONS = {
        "unauthorized": "Card holder claims transaction was unauthorized",
        "duplicate": "Duplicate transaction",
        "not_received": "Goods/services not received",
        "not_as_described": "Goods/services not as described",
        "service_cancelled": "User cancelled service",
        "billing_error": "Billing error",
        "fraudulent": "Fraudulent transaction",
        "processing_error": "Payment processing error",
        "other": "Other reason",
    }
