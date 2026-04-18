"""Tax reporting and jurisdiction tracking models."""

from datetime import datetime, timezone

from sqlalchemy import JSON, Boolean, Column, DateTime, Float, ForeignKey, String

from app.models.base import BaseModel


class TaxReport(BaseModel):
    """Tax reporting by jurisdiction."""

    __tablename__ = "tax_reports"

    period = Column(String, nullable=False, index=True)  # YYYY-MM or YYYY-Q1/Q2/Q3/Q4
    jurisdiction = Column(
        String, nullable=False, index=True
    )  # US, GB, NG, etc. or US-CA, US-NY
    report_type = Column(String, nullable=False)  # VAT, GST, INCOME, WITHHOLDING

    # Revenue tracking
    gross_revenue = Column(Float, nullable=False, default=0.0)
    taxable_revenue = Column(Float, nullable=False, default=0.0)
    tax_exempt_revenue = Column(Float, nullable=False, default=0.0)
    refunded_revenue = Column(Float, nullable=False, default=0.0)

    # Tax calculations
    tax_rate = Column(Float, nullable=False)  # As decimal (0.15 = 15%)
    tax_amount_due = Column(Float, nullable=False, default=0.0)
    tax_paid = Column(Float, nullable=False, default=0.0)
    tax_balance = Column(Float, nullable=False, default=0.0)

    # VAT/GST specific
    vat_input_tax = Column(Float, default=0.0)  # VAT on purchases
    vat_output_tax = Column(Float, default=0.0)  # VAT on sales
    vat_net = Column(Float, default=0.0)  # Output - Input

    # Withholding tax
    withholding_tax_rate = Column(Float, default=0.0)
    gross_withholding = Column(Float, default=0.0)
    net_after_withholding = Column(Float, default=0.0)

    # Transaction breakdown
    transaction_count = Column(Float, default=0)
    services_breakdown = Column(JSON)  # {service: amount}
    customer_breakdown = Column(JSON)  # {user_id: amount}

    # Status & filing
    status = Column(
        String, default="draft", nullable=False, index=True
    )  # draft, pending_review, filed, paid
    filed_at = Column(DateTime)
    filed_with = Column(String)  # Tax authority name
    filing_reference = Column(String)  # Reference number from authority
    due_date = Column(DateTime, nullable=False)
    payment_due_date = Column(DateTime)

    # Payment tracking
    payment_status = Column(
        String, default="unpaid"
    )  # unpaid, partial, paid, overdue, exempted
    payment_date = Column(DateTime)
    payment_method = Column(String)  # bank_transfer, check, etc.
    payment_reference = Column(String)  # Payment confirmation

    # Notes & audit
    notes = Column(String)
    prepared_by = Column(String)  # User or system
    prepared_at = Column(DateTime)
    reviewed_by = Column(String)  # Reviewer or accountant
    reviewed_at = Column(DateTime)


class TaxJurisdictionConfig(BaseModel):
    """Configuration for tax rates and rules by jurisdiction."""

    __tablename__ = "tax_jurisdiction_configs"

    jurisdiction_code = Column(String, nullable=False, unique=True, index=True)
    jurisdiction_name = Column(String, nullable=False)
    country_code = Column(String, index=True)
    state_code = Column(String)  # For US states

    # Tax rates
    standard_tax_rate = Column(Float, nullable=False)  # Standard VAT/GST rate
    reduced_tax_rate = Column(Float, default=0.0)  # Reduced rate if applicable
    zero_tax_rate = Column(Float, default=0.0)  # Zero-rated items

    # Thresholds
    registration_threshold = Column(Float)  # Revenue threshold for registration
    filing_frequency = Column(String)  # monthly, quarterly, annual
    payment_terms_days = Column(Float, default=30)  # Days after due to pay

    # Rules
    requires_vat_registration = Column(Boolean, default=False)
    requires_tax_id = Column(Boolean, default=False)
    requires_reporting = Column(Boolean, default=False)
    is_physical_presence = Column(Boolean, default=False)

    # Categories
    taxable_services = Column(JSON)  # List of services subject to tax
    exempt_services = Column(JSON)  # List of exempt services
    reverse_charge_applies = Column(Boolean, default=False)

    # Filing details
    filing_deadline_days = Column(Float)  # Days after period end
    payment_deadline_days = Column(Float)  # Days after filing for payment
    currency = Column(String, default="USD")

    # Active status
    is_active = Column(Boolean, default=True)
    effective_from = Column(DateTime, nullable=False)
    effective_to = Column(DateTime)

    # Notes
    notes = Column(String)
    last_updated = Column(DateTime)
    updated_by = Column(String)


class TaxExemptionCertificate(BaseModel):
    """Tax exemption certificates for users."""

    __tablename__ = "tax_exemption_certificates"

    user_id = Column(String, ForeignKey("users.id"), nullable=False, index=True)
    jurisdiction = Column(String, nullable=False, index=True)

    # Certificate details
    certificate_number = Column(String, nullable=False, unique=True, index=True)
    certificate_type = Column(
        String, nullable=False
    )  # nonprofit, government, educational, reseller
    exemption_reason = Column(String, nullable=False)

    # Validity
    issued_date = Column(DateTime, nullable=False)
    expiry_date = Column(DateTime, nullable=False, index=True)
    is_valid = Column(Boolean, default=True)

    # Verification
    verified_at = Column(DateTime)
    verified_by = Column(String)
    verification_notes = Column(String)

    # Application
    applied_to_transactions = Column(JSON)  # Transaction IDs using this exemption
    revenue_exempted = Column(Float, default=0.0)


class WithholdingTaxRecord(BaseModel):
    """Track withholding tax obligations (especially for international payments)."""

    __tablename__ = "withholding_tax_records"

    payee_id = Column(String, nullable=False, index=True)  # User or provider ID
    payer_id = Column(String, nullable=False, index=True)  # Organization ID
    jurisdiction = Column(String, nullable=False, index=True)

    # Transaction
    transaction_id = Column(String, nullable=False, index=True)
    payment_date = Column(DateTime, nullable=False)
    gross_amount = Column(Float, nullable=False)

    # Withholding calculation
    withholding_rate = Column(Float, nullable=False)
    withholding_amount = Column(Float, nullable=False)
    net_payment = Column(Float, nullable=False)

    # Tax details
    form_type = Column(String)  # W-9, 1042-S, etc.
    tax_id = Column(String)  # TIN, ITIN, etc.
    country_of_residence = Column(String)

    # Status
    withheld = Column(Boolean, default=False)
    withholding_date = Column(DateTime)
    remitted_to_authority = Column(Boolean, default=False)
    remittance_date = Column(DateTime)
    remittance_reference = Column(String)

    # Notes
    notes = Column(String)
