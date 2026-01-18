"""KYC request/response schemas."""

from datetime import datetime, date
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, validator, Field


class KYCProfileCreate(BaseModel):
    """Schema for creating KYC profile."""

    full_name: str = Field(..., min_length=2, max_length=100)
    phone_number: str = Field(..., min_length=10, max_length=20)
    date_of_birth: date = Field(...)
    nationality: str = Field(..., min_length=2, max_length=3)

    address_line1: str = Field(..., min_length=5, max_length=200)
    address_line2: Optional[str] = Field(None, max_length=200)
    city: str = Field(..., min_length=2, max_length=100)
    state: str = Field(..., min_length=2, max_length=100)
    postal_code: str = Field(..., min_length=3, max_length=20)
    country: str = Field(..., min_length=2, max_length=3)

    @validator("date_of_birth")
    def validate_age(cls, v):
        today = date.today()
        age = today.year - v.year - ((today.month, today.day) < (v.month, v.day))
        if age < 18:
            raise ValueError("Must be at least 18 years old")
        if age > 120:
            raise ValueError("Invalid date of birth")
        return v

    @validator("phone_number")
    def validate_phone(cls, v):
        import re

        # Basic phone validation
        if not re.match(r"^\+?[1 - 9]\d{1,14}$", v.replace(" ", "").replace("-", "")):
            raise ValueError("Invalid phone number format")
        return v

    model_config = {
        "json_schema_extra": {
            "example": {
                "full_name": "John Doe",
                "phone_number": "+1234567890",
                "date_of_birth": "1990 - 01-01",
                "nationality": "US",
                "address_line1": "123 Main Street",
                "address_line2": "Apt 4B",
                "city": "New York",
                "state": "NY",
                "postal_code": "10001",
                "country": "US",
            }
        }
    }


class KYCProfileResponse(BaseModel):
    """Schema for KYC profile response."""

    id: str
    user_id: str
    status: str
    verification_level: str
    full_name: Optional[str]
    phone_number: Optional[str]
    date_of_birth: Optional[date]
    nationality: Optional[str]
    country: Optional[str]
    risk_score: float
    aml_status: str
    pep_status: bool
    submitted_at: Optional[datetime]
    verified_at: Optional[datetime]
    rejected_at: Optional[datetime]
    rejection_reason: Optional[str]
    created_at: datetime

    model_config = {
        "from_attributes": True,
        "json_schema_extra": {
            "example": {
                "id": "kyc_1642680000000",
                "user_id": "user_1642680000000",
                "status": "verified",
                "verification_level": "enhanced",
                "full_name": "John Doe",
                "phone_number": "+1234567890",
                "date_of_birth": "1990 - 01-01",
                "nationality": "US",
                "country": "US",
                "risk_score": 0.2,
                "aml_status": "clear",
                "pep_status": False,
                "submitted_at": "2024 - 01-20T10:00:00Z",
                "verified_at": "2024 - 01-20T15:30:00Z",
                "created_at": "2024 - 01-20T10:00:00Z",
            }
        },
    }


class KYCDocumentResponse(BaseModel):
    """Schema for KYC document response."""

    id: str
    document_type: str
    verification_status: str
    confidence_score: float
    file_name: Optional[str]
    file_size: Optional[float]
    uploaded_at: datetime

    model_config = {
        "from_attributes": True,
        "json_schema_extra": {
            "example": {
                "id": "doc_1642680000000",
                "document_type": "passport",
                "verification_status": "verified",
                "confidence_score": 0.95,
                "file_name": "passport.jpg",
                "file_size": 2048000,
                "uploaded_at": "2024 - 01-20T10:00:00Z",
            }
        },
    }


class KYCVerificationDecision(BaseModel):
    """Schema for admin KYC verification decision."""

    decision: str = Field(..., pattern="^(approved|rejected)$")
    verification_level: Optional[str] = Field("basic", pattern="^(basic|enhanced|premium)$")
    notes: Optional[str] = Field(None, max_length=1000)

    model_config = {
        "json_schema_extra": {
            "example": {
                "decision": "approved",
                "verification_level": "enhanced",
                "notes": "All documents verified successfully",
            }
        }
    }


class KYCLimitsResponse(BaseModel):
    """Schema for KYC limits response."""

    verification_level: str
    daily_limit: float
    monthly_limit: float
    annual_limit: float
    allowed_services: List[str]
    max_transaction_amount: Optional[float]
    current_usage: Dict[str, float]

    model_config = {
        "json_schema_extra": {
            "example": {
                "verification_level": "enhanced",
                "daily_limit": 1000.0,
                "monthly_limit": 5000.0,
                "annual_limit": 50000.0,
                "allowed_services": ["basic", "premium", "enterprise"],
                "max_transaction_amount": 500.0,
                "current_usage": {"daily": 150.0, "monthly": 800.0, "annual": 2500.0},
            }
        }
    }


class AMLScreeningResponse(BaseModel):
    """Schema for AML screening response."""

    id: str
    screening_type: str
    status: str
    match_score: float
    matches_found: List[Dict[str, Any]]
    reviewed_by: Optional[str]
    review_decision: Optional[str]
    created_at: datetime

    model_config = {
        "from_attributes": True,
        "json_schema_extra": {
            "example": {
                "id": "aml_1642680000000",
                "screening_type": "sanctions",
                "status": "clear",
                "match_score": 0.1,
                "matches_found": [],
                "reviewed_by": None,
                "review_decision": None,
                "created_at": "2024 - 01-20T10:00:00Z",
            }
        },
    }


class KYCStatsResponse(BaseModel):
    """Schema for KYC statistics response."""

    total_profiles: int
    verified_profiles: int
    pending_profiles: int
    rejected_profiles: int
    verification_rate: float
    level_distribution: Dict[str, int]

    model_config = {
        "json_schema_extra": {
            "example": {
                "total_profiles": 1000,
                "verified_profiles": 850,
                "pending_profiles": 100,
                "rejected_profiles": 50,
                "verification_rate": 85.0,
                "level_distribution": {"basic": 500, "enhanced": 300, "premium": 50},
            }
        }
    }


class BiometricVerificationRequest(BaseModel):
    """Schema for biometric verification request."""

    verification_type: str = Field(..., pattern="^(face_match|liveness|voice)$")
    reference_document_id: Optional[str] = None

    model_config = {
        "json_schema_extra": {
            "example": {
                "verification_type": "face_match",
                "reference_document_id": "doc_1642680000000",
            }
        }
    }


class BiometricVerificationResponse(BaseModel):
    """Schema for biometric verification response."""

    id: str
    verification_type: str
    verification_result: str
    match_score: Optional[float]
    liveness_score: Optional[float]
    confidence_level: str
    created_at: datetime

    model_config = {
        "from_attributes": True,
        "json_schema_extra": {
            "example": {
                "id": "bio_1642680000000",
                "verification_type": "face_match",
                "verification_result": "pass",
                "match_score": 0.92,
                "liveness_score": 0.88,
                "confidence_level": "high",
                "created_at": "2024 - 01-20T10:00:00Z",
            }
        },
    }


class KYCAuditLogResponse(BaseModel):
    """Schema for KYC audit log response."""

    id: str
    user_id: str
    action: str
    old_status: Optional[str]
    new_status: Optional[str]
    admin_id: Optional[str]
    reason: Optional[str]
    ip_address: Optional[str]
    created_at: datetime

    model_config = {
        "from_attributes": True,
        "json_schema_extra": {
            "example": {
                "id": "audit_1642680000000",
                "user_id": "user_1642680000000",
                "action": "status_changed",
                "old_status": "pending",
                "new_status": "verified",
                "admin_id": "admin_1642680000000",
                "reason": "All documents verified",
                "ip_address": "192.168.1.1",
                "created_at": "2024 - 01-20T10:00:00Z",
            }
        },
    }


class DocumentUploadResponse(BaseModel):
    """Schema for document upload response."""

    id: str
    document_type: str
    status: str
    file_name: str
    file_size: float
    upload_url: Optional[str]
    processing_status: str
    uploaded_at: datetime

    model_config = {
        "json_schema_extra": {
            "example": {
                "id": "doc_1642680000000",
                "document_type": "passport",
                "status": "uploaded",
                "file_name": "passport.jpg",
                "file_size": 2048000,
                "upload_url": None,
                "processing_status": "pending",
                "uploaded_at": "2024 - 01-20T10:00:00Z",
            }
        }
    }


class KYCComplianceReport(BaseModel):
    """Schema for KYC compliance report."""

    report_id: str
    report_type: str
    period_start: date
    period_end: date
    total_verifications: int
    compliance_rate: float
    risk_distribution: Dict[str, int]
    aml_alerts: int
    generated_at: datetime

    model_config = {
        "json_schema_extra": {
            "example": {
                "report_id": "report_1642680000000",
                "report_type": "monthly",
                "period_start": "2024 - 01-01",
                "period_end": "2024 - 01-31",
                "total_verifications": 500,
                "compliance_rate": 98.5,
                "risk_distribution": {"low": 450, "medium": 40, "high": 10},
                "aml_alerts": 5,
                "generated_at": "2024 - 02-01T00:00:00Z",
            }
        }
    }
