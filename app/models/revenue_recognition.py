"""Revenue recognition models for GAAP compliance."""

from datetime import datetime, timezone

from sqlalchemy import JSON, Boolean, Column, DateTime, Float, ForeignKey, String

from app.models.base import BaseModel


class RevenueRecognition(BaseModel):
    """Track revenue recognition for accounting standards compliance."""

    __tablename__ = "revenue_recognitions"

    transaction_id = Column(
        String,
        ForeignKey("sms_transactions.id"),
        nullable=False,
        index=True,
        unique=True,
    )
    user_id = Column(String, ForeignKey("users.id"), nullable=False, index=True)

    # Revenue amounts
    gross_amount = Column(Float, nullable=False)  # Total revenue
    net_amount = Column(Float, nullable=False)  # After provider costs
    provider_cost = Column(Float, nullable=False)  # Cost paid to provider

    # Recognition timing
    transaction_date = Column(DateTime, nullable=False, index=True)
    revenue_recognized_date = Column(DateTime, nullable=False, index=True)
    revenue_period = Column(String, nullable=False)  # YYYY-MM for monthly bucketing

    # Recognition status
    status = Column(
        String, default="pending", nullable=False, index=True
    )  # pending, recognized, reversed

    # Service & categorization
    service_type = Column(String, nullable=False)
    transaction_category = Column(
        String, nullable=False
    )  # verification, topup, purchase, refund
    tax_jurisdiction = Column(String, nullable=False)  # Country/State code

    # Accrual vs cash basis
    is_cash_basis = Column(Boolean, default=True)
    is_accrual_basis = Column(Boolean, default=False)

    # Deferral tracking
    deferred_amount = Column(Float, default=0.0)  # Amount deferred
    deferral_period = Column(
        String
    )  # e.g., "2024-01" to "2024-12" for service subscriptions
    deferral_reversal_date = Column(DateTime)  # When deferred revenue recognizes

    # Reconciliation
    matches_expected_revenue = Column(Boolean, default=True)
    variance_amount = Column(Float, default=0.0)
    variance_reason = Column(String)

    # Audit trail
    recognized_by = Column(String)  # System or admin
    reversal_date = Column(DateTime)  # If reversed
    reversal_reason = Column(String)
    reversal_notes = Column(String)

    # Metadata
    journal_entry_id = Column(String)  # Link to accounting system
    notes = Column(String)


class DeferredRevenueSchedule(BaseModel):
    """Track deferred revenue schedules for long-term contracts."""

    __tablename__ = "deferred_revenue_schedules"

    user_id = Column(String, ForeignKey("users.id"), nullable=False, index=True)
    contract_id = Column(String, nullable=False, index=True)
    contract_start_date = Column(DateTime, nullable=False)
    contract_end_date = Column(DateTime, nullable=False)

    # Amount tracking
    total_contract_value = Column(Float, nullable=False)
    monthly_recognition_amount = Column(Float, nullable=False)
    months_remaining = Column(Float, nullable=False)

    # Recognition schedule
    schedule = Column(JSON)  # Array of {month: "YYYY-MM", amount: X, recognized: bool}
    total_recognized = Column(Float, default=0.0)
    total_remaining = Column(Float, nullable=False)

    # Status
    status = Column(
        String, default="active", nullable=False
    )  # active, completed, cancelled
    cancellation_reason = Column(String)
    cancellation_date = Column(DateTime)

    # Adjustment tracking
    adjustments = Column(JSON)  # Array of {date, reason, amount, type}
    last_adjusted = Column(DateTime)
    adjusted_by = Column(String)


class RevenueAdjustment(BaseModel):
    """Revenue adjustments for corrections, refunds, and disputes."""

    __tablename__ = "revenue_adjustments"

    original_revenue_id = Column(
        String, ForeignKey("revenue_recognitions.id"), nullable=False, index=True
    )
    user_id = Column(String, ForeignKey("users.id"), nullable=False, index=True)
    transaction_id = Column(String, nullable=False, index=True)

    # Adjustment details
    adjustment_type = Column(
        String, nullable=False
    )  # refund, chargeback, dispute, correction, writeoff
    adjustment_reason = Column(String, nullable=False)

    # Amounts
    original_amount = Column(Float, nullable=False)
    adjusted_amount = Column(Float, nullable=False)
    adjustment_delta = Column(Float, nullable=False)  # Amount of change

    # Timing
    adjustment_date = Column(DateTime, nullable=False, index=True)
    adjustment_period = Column(String, nullable=False)  # YYYY-MM

    # Impact on revenue
    revenue_impact = Column(String, nullable=False)  # increase or decrease
    accounting_entry = Column(String)  # Debit/Credit notation

    # Tracking
    initiated_by = Column(String, nullable=False)  # User ID or system
    approval_status = Column(String, default="pending")  # pending, approved, rejected
    approved_by = Column(String)
    approved_at = Column(DateTime)

    # Audit
    notes = Column(String)
    supporting_documentation = Column(JSON)  # Links to evidence
    reversal_date = Column(DateTime)  # If reversed


class AccrualTrackingLog(BaseModel):
    """Log all accrual adjustments for reconciliation."""

    __tablename__ = "accrual_tracking_logs"

    user_id = Column(String, ForeignKey("users.id"), nullable=True, index=True)
    account_type = Column(
        String, nullable=False, index=True
    )  # revenue, expense, liability

    # Accrual details
    period = Column(String, nullable=False, index=True)  # YYYY-MM
    accrual_date = Column(DateTime, nullable=False)
    accrual_type = Column(
        String, nullable=False
    )  # billed_not_received, received_not_billed, liability

    # Amounts
    accrued_amount = Column(Float, nullable=False)
    actual_amount = Column(Float, nullable=False)
    variance = Column(Float, nullable=False)

    # Status
    status = Column(String, default="open", nullable=False)  # open, reversed, settled
    settled_at = Column(DateTime)
    settlement_notes = Column(String)

    # Reconciliation
    matched_to_transaction = Column(String)  # Transaction ID if matched
    reconciliation_notes = Column(String)
