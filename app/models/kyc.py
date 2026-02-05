"""KYC (Know Your Customer) database models."""

from sqlalchemy import JSON, Boolean, Column, Date, DateTime, Float, String, Text

from app.models.base import BaseModel


class KYCProfile(BaseModel):
    """KYC profile for user identity verification."""

    __tablename__ = "kyc_profiles"

    user_id = Column(String, unique=True, nullable=False, index=True)
    status = Column(String, default="unverified", nullable=False, index=True)  # unverified/pending/verified/rejected
    verification_level = Column(String, default="basic", nullable=False)  # basic/enhanced/premium

    # Personal Information
    full_name = Column(String)
    phone_number = Column(String)
    date_of_birth = Column(Date)
    nationality = Column(String)

    # Address Information
    address_line1 = Column(String)
    address_line2 = Column(String)
    city = Column(String)
    state = Column(String)
    postal_code = Column(String)
    country = Column(String)

    # Verification Timestamps
    submitted_at = Column(DateTime)
    verified_at = Column(DateTime)
    rejected_at = Column(DateTime)
    rejection_reason = Column(Text)

    # Risk Assessment
    risk_score = Column(Float, default=0.0, nullable=False)
    aml_status = Column(String, default="pending")  # pending/clear/flagged
    pep_status = Column(Boolean, default=False)  # Politically Exposed Person

    # Additional Metadata
    ip_address = Column(String)
    user_agent = Column(String)
    verification_notes = Column(Text)


class KYCDocument(BaseModel):
    """KYC document storage and verification."""

    __tablename__ = "kyc_documents"

    kyc_profile_id = Column(String, nullable=False, index=True)
    document_type = Column(String, nullable=False)  # passport/license/id_card/utility_bill/selfie
    document_number = Column(String)
    document_expiry = Column(Date)

    # File Information
    file_path = Column(String, nullable=False)
    file_name = Column(String)
    file_size = Column(Float)
    file_hash = Column(String, unique=True)
    mime_type = Column(String)

    # Verification Status
    verification_status = Column(String, default="pending", nullable=False)  # pending/verified/rejected
    verification_method = Column(String)  # manual/automated/hybrid
    confidence_score = Column(Float, default=0.0)

    # Extracted Data
    extracted_data = Column(JSON)
    ocr_text = Column(Text)

    # Security
    is_encrypted = Column(Boolean, default=True)
    access_count = Column(Float, default=0)
    last_accessed = Column(DateTime)


class KYCVerificationLimit(BaseModel):
    """Transaction limits based on KYC verification level."""

    __tablename__ = "kyc_verification_limits"

    verification_level = Column(String, unique=True, nullable=False)
    daily_limit = Column(Float, nullable=False)
    monthly_limit = Column(Float, nullable=False)
    annual_limit = Column(Float, nullable=False)

    # Service Access
    allowed_services = Column(JSON)  # List of allowed service types
    max_transaction_amount = Column(Float)
    requires_additional_auth = Column(Boolean, default=False)

    # Restrictions
    country_restrictions = Column(JSON)  # List of restricted countries
    service_restrictions = Column(JSON)  # List of restricted services


class KYCAuditLog(BaseModel):
    """Audit trail for all KYC - related actions."""

    __tablename__ = "kyc_audit_logs"

    user_id = Column(String, nullable=False, index=True)
    action = Column(String, nullable=False)  # profile_created/document_uploaded/status_changed/etc

    # Status Changes
    old_status = Column(String)
    new_status = Column(String)
    old_level = Column(String)
    new_level = Column(String)

    # Actor Information
    admin_id = Column(String)  # If action performed by admin
    system_action = Column(Boolean, default=False)  # If automated action

    # Context
    reason = Column(Text)
    details = Column(JSON)

    # Security Context
    ip_address = Column(String)
    user_agent = Column(String)
    session_id = Column(String)


class AMLScreening(BaseModel):
    """Anti - Money Laundering screening results."""

    __tablename__ = "aml_screenings"

    kyc_profile_id = Column(String, nullable=False, index=True)
    screening_type = Column(String, nullable=False)  # sanctions/pep/adverse_media

    # Screening Results
    status = Column(String, default="pending")  # pending/clear/match/review
    match_score = Column(Float, default=0.0)
    matches_found = Column(JSON)  # List of potential matches

    # Screening Details
    search_terms = Column(JSON)
    data_sources = Column(JSON)
    screening_provider = Column(String)

    # Review Information
    reviewed_by = Column(String)
    review_decision = Column(String)  # clear/escalate/block
    review_notes = Column(Text)
    reviewed_at = Column(DateTime)


class KYCSettings(BaseModel):
    """Global KYC configuration settings."""

    __tablename__ = "kyc_settings"

    setting_key = Column(String, unique=True, nullable=False)
    setting_value = Column(JSON, nullable=False)
    description = Column(Text)

    # Metadata
    updated_by = Column(String)
    is_active = Column(Boolean, default=True)


class BiometricVerification(BaseModel):
    """Biometric verification records."""

    __tablename__ = "biometric_verifications"

    kyc_profile_id = Column(String, nullable=False, index=True)
    verification_type = Column(String, nullable=False)  # face_match/liveness/voice

    # Verification Data
    reference_image_path = Column(String)  # ID photo
    verification_image_path = Column(String)  # Selfie
    match_score = Column(Float)
    liveness_score = Column(Float)

    # Results
    verification_result = Column(String)  # pass/fail/review
    confidence_level = Column(String)  # low/medium/high

    # Technical Details
    algorithm_used = Column(String)
    processing_time = Column(Float)
    quality_scores = Column(JSON)