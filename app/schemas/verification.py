"""Verification request/response schemas with enhanced validation."""

import re
from datetime import datetime
from typing import List, Optional

from app.core.pydantic_compat import BaseModel, Field, field_validator


class VerificationRequest(BaseModel):
    """Request to purchase SMS verification.

    Filters: country (required) + city (optional).
    Carrier filtering has been retired.
    """

    service: str = Field(
        ...,
        min_length=1,
        max_length=50,
        description="Service name (telegram, whatsapp, etc)",
    )
    country: str = Field(
        default="US", min_length=2, max_length=3, description="ISO country code"
    )
    capability: str = Field(default="sms", description="sms or voice")
    city: Optional[str] = Field(
        default=None,
        max_length=100,
        description="City for number selection. Pro/Custom: precise. PAYG: best-effort.",
    )
    area_codes: Optional[List[str]] = Field(
        default=None, description="US area codes (internal use, derived from city)"
    )
    idempotency_key: Optional[str] = Field(
        default=None,
        min_length=36,
        max_length=36,
        description="UUID v4 idempotency key",
    )

    @field_validator("service", mode="before")
    @classmethod
    def validate_service(cls, v):
        """Validate and normalize service names."""
        if not isinstance(v, str):
            raise ValueError("Service must be a string")

        # Sanitize input
        v = v.strip().lower()

        # Allow only alphanumeric, underscore, hyphen
        if not re.match(r"^[a-zA-Z0-9_-]+$", v):
            raise ValueError("Service name contains invalid characters")

        # Check against known services
        allowed_services = {
            "telegram",
            "whatsapp",
            "discord",
            "instagram",
            "facebook",
            "google",
            "twitter",
            "microsoft",
            "amazon",
            "uber",
            "netflix",
            "spotify",
            "tiktok",
            "snapchat",
            "linkedin",
            "github",
            "paypal",
        }

        if v not in allowed_services:
            # Allow unknown services but log for monitoring
            pass

        return v

    @field_validator("country", mode="before")
    @classmethod
    def validate_country(cls, v):
        """Validate and normalize country codes."""
        if not isinstance(v, str):
            raise ValueError("Country must be a string")

        v = v.strip().upper()

        # Validate ISO country code format
        if not re.match(r"^[A-Z]{2,3}$", v):
            raise ValueError("Invalid country code format")

        country_map = {
            "USA": "US",
            "UNITED STATES": "US",
            "CANADA": "CA",
            "UK": "GB",
            "UNITED KINGDOM": "GB",
            "RUSSIA": "RU",
            "INDIA": "IN",
            "GERMANY": "DE",
            "FRANCE": "FR",
        }

        return country_map.get(v, v)

    @field_validator("capability", mode="before")
    @classmethod
    def validate_capability(cls, v):
        """Validate capability type."""
        if not isinstance(v, str):
            raise ValueError("Capability must be a string")

        v = v.strip().lower()

        if v not in ["sms", "voice"]:
            raise ValueError("Capability must be 'sms' or 'voice'")

        return v

    @field_validator("city", mode="before")
    @classmethod
    def validate_city(cls, v):
        """Validate and normalize city name."""
        if v is None:
            return v
        if not isinstance(v, str):
            raise ValueError("City must be a string")
        v = v.strip()
        if len(v) == 0:
            return None
        if len(v) > 100:
            raise ValueError("City name too long")
        return v

    @field_validator("area_codes", mode="before")
    @classmethod
    def validate_area_codes(cls, v):
        """Validate area codes format (US only, internal use)."""
        if v is None:
            return v
        if not isinstance(v, list):
            raise ValueError("Area codes must be a list")
        validated_codes = []
        for code in v:
            if not isinstance(code, str):
                raise ValueError("Area code must be a string")
            code = code.strip()
            if not re.match(r"^\d{3}$", code):
                raise ValueError(f"Invalid area code format: {code}")
            validated_codes.append(code)
        return validated_codes[:10]

    @field_validator("idempotency_key", mode="before")
    @classmethod
    def validate_idempotency_key(cls, v):
        """Validate UUID v4 idempotency key."""
        if v is None:
            return v

        if not isinstance(v, str):
            raise ValueError("Idempotency key must be a string")

        # UUID v4 format validation
        uuid_pattern = (
            r"^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$"
        )
        if not re.match(uuid_pattern, v.lower()):
            raise ValueError("Idempotency key must be a valid UUID v4")

        return v.lower()


class VerificationResponse(BaseModel):
    """Response after purchasing verification."""

    verification_id: str
    phone_number: str
    service: str
    country: str
    cost: float
    status: str
    activation_id: str


class VerificationDetail(BaseModel):
    """Detailed verification information."""

    id: str
    phone_number: str
    service: str
    country: str
    status: str
    sms_code: Optional[str] = None
    sms_text: Optional[str] = None
    cost: float
    created_at: datetime
    completed_at: Optional[datetime] = None
    sms_received_at: Optional[datetime] = None


class VerificationHistory(BaseModel):
    """Verification history item."""

    id: str
    phone_number: str
    service: str
    country: str
    status: str
    cost: float
    created_at: datetime
    completed_at: Optional[datetime] = None


class VerificationHistoryResponse(BaseModel):
    """Verification history response."""

    total: int
    skip: int
    limit: int
    verifications: List[VerificationHistory]


class ReleaseResponse(BaseModel):
    """Response after releasing verification."""

    success: bool
    message: str
    verification_id: str
    status: str


class NumberRentalRequest(BaseModel):
    """Request to rent a phone number."""

    service: str = Field(..., description="Service name")
    country: str = Field(default="US", description="Country code")
    duration_days: int = Field(default=30, description="Rental duration in days")
    renewable: bool = Field(default=False, description="Whether rental is renewable")


class NumberRentalResponse(BaseModel):
    """Response after renting a number."""

    rental_id: str
    phone_number: str
    service: str
    country: str
    cost: float
    duration_days: int
    expires_at: datetime
    renewable: bool


class ExtendRentalRequest(BaseModel):
    """Request to extend a rental."""

    rental_id: str = Field(..., description="Rental ID to extend")
    duration_days: int = Field(default=30, description="Additional duration in days")


class RetryVerificationRequest(BaseModel):
    """Request to retry verification."""

    verification_id: str = Field(..., description="Verification ID to retry")


class ServicePriceResponse(BaseModel):
    """Service pricing information."""

    service: str
    country: str
    price: float
    currency: str


class VerificationCreate(BaseModel):
    """Create verification request."""

    service: str
    country: str = "US"
    capability: str = "sms"


class MessageResponse(BaseModel):
    """Generic message response."""

    message: str
    success: bool = True
