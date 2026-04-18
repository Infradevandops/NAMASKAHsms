"""Provider settlement and payout tracking models."""

from datetime import datetime, timezone

from sqlalchemy import JSON, Boolean, Column, DateTime, Float, ForeignKey, String

from app.models.base import BaseModel


class ProviderSettlement(BaseModel):
    """Track settlement obligations to SMS providers."""

    __tablename__ = "provider_settlements"

    provider_id = Column(String, nullable=False, index=True)
    settlement_period = Column(String, nullable=False, index=True)  # YYYY-MM
    settlement_start = Column(DateTime, nullable=False)
    settlement_end = Column(DateTime, nullable=False)

    # Transaction summary
    total_messages_sent = Column(Float, default=0)
    successful_messages = Column(Float, default=0)
    failed_messages = Column(Float, default=0)
    delivery_rate = Column(Float, default=0.0)  # Percentage

    # Cost breakdown
    per_message_cost = Column(Float, nullable=False)
    total_message_cost = Column(Float, nullable=False)  # messages * rate
    usage_cost = Column(Float, default=0.0)  # API usage fees
    other_fees = Column(Float, default=0.0)  # Setup, platform fees, etc.
    total_cost = Column(Float, nullable=False)

    # Billing details
    currency = Column(String, default="USD")
    invoice_number = Column(String, unique=True)
    invoice_date = Column(DateTime)
    due_date = Column(DateTime, nullable=False)

    # Payment tracking
    status = Column(
        String, default="open", nullable=False, index=True
    )  # open, due, paid, overdue, disputed, cancelled

    paid_amount = Column(Float, default=0.0)
    paid_date = Column(DateTime)
    payment_method = Column(String)  # bank_transfer, card, debit
    payment_reference = Column(String)
    remaining_balance = Column(Float, nullable=False)

    # Discounts & adjustments
    discount_percentage = Column(Float, default=0.0)
    discount_amount = Column(Float, default=0.0)
    adjustments = Column(JSON)  # [{reason, amount, date}]
    total_adjustments = Column(Float, default=0.0)

    # Service details
    services_used = Column(JSON)  # {service: cost}
    countries_covered = Column(JSON)  # List of countries
    special_rates = Column(JSON)  # Any negotiated rates

    # Reconciliation
    messages_per_invoice = Column(Float)  # From provider invoice
    variance_messages = Column(Float, default=0.0)  # Our count - Invoice count
    variance_reason = Column(String)

    # Dispute tracking
    disputed = Column(Boolean, default=False)
    dispute_amount = Column(Float, default=0.0)
    dispute_reason = Column(String)
    dispute_raised_at = Column(DateTime)
    dispute_resolution = Column(
        String
    )  # pending, resolved, awarded_to_us, awarded_to_provider
    dispute_resolved_at = Column(DateTime)

    # Notes & audit
    notes = Column(String)
    created_by = Column(String)
    last_updated = Column(DateTime)
    updated_by = Column(String)


class ProviderCostTracking(BaseModel):
    """Daily cost tracking per provider for real-time visibility."""

    __tablename__ = "provider_cost_tracking"

    provider_id = Column(String, nullable=False, index=True)
    tracking_date = Column(DateTime, nullable=False, index=True)

    # Message counts
    messages_sent = Column(Float, default=0)
    successful_sends = Column(Float, default=0)
    failed_sends = Column(Float, default=0)
    success_rate = Column(Float, default=0.0)

    # Cost tracking
    per_message_rate = Column(Float, nullable=False)
    daily_message_cost = Column(Float, default=0.0)
    daily_fees = Column(Float, default=0.0)
    daily_total_cost = Column(Float, default=0.0)

    # Running totals for period
    period_ytd_cost = Column(Float, default=0.0)  # Year-to-date
    period_mtd_cost = Column(Float, default=0.0)  # Month-to-date
    period_budget = Column(Float, default=0.0)  # Forecasted total
    percent_of_budget = Column(Float, default=0.0)

    # Service breakdown
    service_costs = Column(JSON)  # {service: cost}
    country_costs = Column(JSON)  # {country: cost}

    # Alerts
    approaching_budget = Column(Boolean, default=False)
    budget_threshold_percent = Column(Float, default=80.0)

    # Metadata
    hourly_breakdown = Column(JSON)  # Granular hourly data if available
    notes = Column(String)


class PayoutSchedule(BaseModel):
    """Scheduled payouts to providers."""

    __tablename__ = "payout_schedules"

    provider_id = Column(String, nullable=False, index=True)
    payout_id = Column(String, unique=True, nullable=False)
    settlement_id = Column(
        String, ForeignKey("provider_settlements.id"), nullable=False, index=True
    )

    # Payout details
    payout_amount = Column(Float, nullable=False)
    payout_currency = Column(String, default="USD")
    scheduled_date = Column(DateTime, nullable=False, index=True)
    actual_date = Column(DateTime)

    # Payment routing
    bank_account = Column(String, nullable=False)  # Encrypted
    account_holder = Column(String)
    routing_number = Column(String)
    swift_code = Column(String)

    # Status
    status = Column(
        String, default="scheduled", nullable=False, index=True
    )  # scheduled, processing, completed, failed, reversed

    # Confirmation
    confirmation_number = Column(String)
    batch_id = Column(String)  # Batch processing ID

    # Fee tracking
    transaction_fee = Column(Float, default=0.0)
    exchange_rate = Column(Float, default=1.0)
    net_payout = Column(Float, nullable=False)

    # Retry logic
    retry_count = Column(Float, default=0)
    max_retries = Column(Float, default=3)
    last_retry_date = Column(DateTime)
    failure_reason = Column(String)

    # Notes
    notes = Column(String)
    processed_by = Column(String)


class ProviderReconciliation(BaseModel):
    """Reconciliation between our records and provider invoices."""

    __tablename__ = "provider_reconciliations"

    provider_id = Column(String, nullable=False, index=True)
    settlement_period = Column(String, nullable=False, index=True)  # YYYY-MM
    reconciliation_date = Column(DateTime, nullable=False)

    # Our records
    our_message_count = Column(Float, nullable=False)
    our_total_cost = Column(Float, nullable=False)
    our_success_rate = Column(Float, nullable=False)

    # Provider invoice
    invoice_message_count = Column(Float, nullable=False)
    invoice_total_cost = Column(Float, nullable=False)
    invoice_success_rate = Column(Float, nullable=False)

    # Variance analysis
    message_count_variance = Column(Float)  # Our count - Invoice count
    cost_variance = Column(Float)  # Our cost - Invoice cost
    variance_percentage = Column(Float)  # (Variance / Invoice) * 100
    success_rate_variance = Column(Float)

    # Root cause analysis
    variance_reason = Column(String)
    discrepancies = Column(JSON)  # {issue_type: count}

    # Resolution
    status = Column(
        String, default="pending", nullable=False
    )  # pending, reconciled, disputed
    resolved_at = Column(DateTime)
    resolution_notes = Column(String)
    adjustment_made = Column(Boolean, default=False)
    adjustment_amount = Column(Float, default=0.0)

    # Investigation
    investigation_completed = Column(Boolean, default=False)
    investigated_by = Column(String)
    investigated_at = Column(DateTime)

    # Audit trail
    notes = Column(String)
    supporting_documents = Column(JSON)  # File references


class ProviderAgreement(BaseModel):
    """Provider agreements and rate terms."""

    __tablename__ = "provider_agreements"

    provider_id = Column(String, nullable=False, unique=True, index=True)
    provider_name = Column(String, nullable=False)

    # Agreement terms
    agreement_type = Column(
        String, nullable=False
    )  # master_service, volume_discount, exclusive
    effective_from = Column(DateTime, nullable=False)
    effective_to = Column(DateTime)
    is_active = Column(Boolean, default=True)

    # Pricing
    base_rate_per_message = Column(Float, nullable=False)
    volume_breakpoints = Column(JSON)  # [{volume: X, rate: Y}]
    minimum_monthly_volume = Column(Float, default=0)
    setup_fee = Column(Float, default=0.0)
    platform_fee_percentage = Column(Float, default=0.0)

    # Service terms
    sla_uptime = Column(Float, default=99.9)  # Target uptime %
    max_latency_ms = Column(Float)  # Maximum message latency
    coverage_countries = Column(JSON)  # List of countries
    coverage_regions = Column(JSON)  # List of regions

    # Volume commitments
    minimum_annual_spend = Column(Float, default=0)
    committed_volume = Column(Float, default=0)
    committed_rate = Column(Float)
    overage_rate = Column(Float)

    # Payment terms
    payment_frequency = Column(String)  # daily, weekly, monthly
    payment_method = Column(String)  # bank_transfer, card, etc.
    net_days = Column(Float, default=30)  # Net-30, Net-60, etc.

    # Discounts
    early_payment_discount = Column(Float, default=0.0)  # Percentage
    volume_discount = Column(Float, default=0.0)  # Percentage
    loyalty_discount = Column(Float, default=0.0)  # Percentage

    # Contacts
    primary_contact = Column(String)
    primary_contact_email = Column(String)
    technical_contact = Column(String)
    technical_contact_email = Column(String)

    # Documentation
    agreement_document = Column(String)  # File path/URL
    notes = Column(String)

    # Tracking
    reviewed_at = Column(DateTime)
    reviewed_by = Column(String)
    last_updated = Column(DateTime)
