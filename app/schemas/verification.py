"""Verification request/response schemas."""

from datetime import datetime
from typing import Optional
from app.core.pydantic_compat import BaseModel, Field, field_validator


class VerificationRequest(BaseModel):
    """Request to purchase SMS verification."""

    service: str = Field(..., description="Service name (telegram, whatsapp, etc)")
    country: str = Field(default="US", description="Country code")
    capability: str = Field(default="sms", description="sms or voice")
    area_codes: Optional[list[str]] = Field(
        default=None, description="Preferred area codes"
    )
    carriers: Optional[list[str]] = Field(
        default=None, description="Preferred carriers"
    )
    idempotency_key: Optional[str] = Field(
        default=None, description="Idempotency key to prevent duplicate charges"
    )

    @field_validator("country", mode="before")
    @classmethod
    def normalize_country(cls, v):
        """Normalize country codes to uppercase ISO format."""
        country_map = {
            "usa": "US",
            "united states": "US",
            "us": "US",
            "canada": "CA",
            "ca": "CA",
            "uk": "GB",
            "united kingdom": "GB",
            "gb": "GB",
            "russia": "RU",
            "ru": "RU",
            "india": "IN",
            "in": "IN",
            "germany": "DE",
            "de": "DE",
            "france": "FR",
            "fr": "FR",
        }
        return country_map.get(v.lower(), v.upper())

    @field_validator("service", mode="before")
    @classmethod
    def normalize_service(cls, v):
        """Normalize service names to lowercase."""
        return v.lower().strip()


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
        verifications: list[VerificationHistory]


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