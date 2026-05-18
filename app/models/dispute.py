"""Dispute and chargeback models for payment disputes."""

from datetime import datetime, timezone

from sqlalchemy import Boolean, Column, DateTime, Float, ForeignKey, Integer, String

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


class DisputeComment(BaseModel):
    """Comments on disputes for communication between user and admin."""

    __tablename__ = "dispute_comments"

    dispute_id = Column(String, ForeignKey("disputes.id"), nullable=False, index=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    content = Column(String, nullable=False)
    is_admin = Column(Boolean, default=False, nullable=False)
    created_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
        index=True,
    )


class DisputeAttachment(BaseModel):
    """File attachments for dispute evidence."""

    __tablename__ = "dispute_attachments"

    dispute_id = Column(String, ForeignKey("disputes.id"), nullable=False, index=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    filename = Column(String, nullable=False)
    file_path = Column(String, nullable=False)  # S3 or local path
    file_size = Column(Integer, nullable=False)  # bytes
    content_type = Column(String, nullable=False)
    uploaded_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
        index=True,
    )


class DisputeTimeline(BaseModel):
    """Timeline events for dispute tracking."""

    __tablename__ = "dispute_timeline"

    dispute_id = Column(String, ForeignKey("disputes.id"), nullable=False, index=True)
    event_type = Column(
        String, nullable=False
    )  # opened, comment_added, evidence_uploaded, status_changed, resolved
    event_description = Column(String, nullable=False)
    actor_id = Column(String)  # User or admin who triggered event
    is_admin = Column(Boolean, default=False)
    event_metadata = Column(String)  # JSON for additional data (renamed from metadata)
    created_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
        index=True,
    )
