"""Reconciliation log model for financial reconciliation tracking."""

from datetime import datetime, timezone

from sqlalchemy import JSON, Boolean, Column, DateTime, Float, ForeignKey, String

from app.models.base import BaseModel


class ReconciliationLog(BaseModel):
    """Reconciliation tracking for wallet and transaction balances."""

    __tablename__ = "reconciliation_logs"

    user_id = Column(String, ForeignKey("users.id"), nullable=True, index=True)
    account_type = Column(
        String, nullable=False, index=True
    )  # user_wallet, payment_account, provider_account

    # Reconciliation scope
    reconciliation_period = Column(DateTime, nullable=False, index=True)  # Start date
    reconciliation_end = Column(DateTime, nullable=False, index=True)  # End date

    # Expected vs actual values
    expected_balance = Column(Float, nullable=False)
    actual_balance = Column(Float, nullable=False)
    discrepancy_amount = Column(Float, nullable=False)  # actual - expected

    # Reconciliation status
    status = Column(
        String,
        default="pending",
        nullable=False,
        index=True,
    )  # pending, in_progress, reconciled, failed, manual_override

    # Details
    total_debits = Column(Float, default=0.0)
    total_credits = Column(Float, default=0.0)
    transaction_count = Column(Float, default=0.0)

    # Discrepancy details
    discrepancy_type = Column(String)  # missing_transaction, duplicate, amount_mismatch
    affected_transactions = Column(JSON)  # Array of transaction IDs with issues

    # Resolution
    resolution = Column(String)  # auto_resolved, manual_resolved, not_resolved
    resolution_notes = Column(String)
    resolved_by = Column(String)  # User ID or 'system'
    resolved_at = Column(DateTime)

    # Automatic detection settings
    threshold_percentage = Column(Float, default=1.0)  # Alert if > 1% difference
    is_critical = Column(
        Boolean, default=False
    )  # Flag for large discrepancies requiring attention

    # Retry tracking
    retry_count = Column(Float, default=0.0)
    next_reconciliation_at = Column(DateTime)

    # Created and updated timestamps
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
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)


class BalanceMismatchAlert(BaseModel):
    """Alert for balance mismatches requiring investigation."""

    __tablename__ = "balance_mismatch_alerts"

    user_id = Column(String, ForeignKey("users.id"), nullable=False, index=True)
    mismatch_amount = Column(Float, nullable=False)
    percentage_diff = Column(Float, nullable=False)

    # Expected vs actual
    expected_balance = Column(Float, nullable=False)
    actual_balance = Column(Float, nullable=False)

    # Investigation
    status = Column(
        String, default="open", nullable=False, index=True
    )  # open, investigating, resolved, dismissed
    root_cause = Column(String)
    resolution_notes = Column(String)

    # Timeline
    detected_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
        index=True,
    )
    last_checked_at = Column(DateTime)
    resolved_at = Column(DateTime)
    resolved_by = Column(String)  # Admin user_id

    # Severity
    severity = Column(
        String, default="medium", nullable=False
    )  # low, medium, high, critical
    requires_manual_review = Column(Boolean, default=False)
