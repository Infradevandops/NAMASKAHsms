"""Verification status response schemas for enterprise-grade API."""

from datetime import datetime
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field


class VerificationStatus(str, Enum):
    """Verification status enumeration."""

    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    EXPIRED = "expired"
    CANCELLED = "cancelled"


class VerificationStatusResponse(BaseModel):
    """Enterprise-grade verification status response."""

    # Core fields
    verification_id: str = Field(..., description="Unique verification ID")
    status: VerificationStatus = Field(..., description="Current verification status")
    phone_number: str = Field(..., description="Phone number for verification")

    # SMS details
    sms_code: Optional[str] = Field(
        None, description="SMS verification code (if received)"
    )
    sms_text: Optional[str] = Field(None, description="Full SMS message text")
    sms_received_at: Optional[datetime] = Field(
        None, description="Timestamp when SMS was received"
    )

    # Service details
    service: str = Field(..., description="Service name")
    country: str = Field(..., description="Country code")
    cost: float = Field(..., description="Cost in USD")

    # Timestamps
    created_at: datetime = Field(..., description="Verification creation timestamp")
    completed_at: Optional[datetime] = Field(
        None, description="Verification completion timestamp"
    )
    expires_at: Optional[datetime] = Field(
        None, description="Verification expiration timestamp"
    )

    # Metadata
    activation_id: Optional[str] = Field(None, description="Provider activation ID")
    provider: str = Field("textverified", description="SMS provider name")

    # Additional info
    retry_count: int = Field(0, description="Number of retry attempts")
    error_message: Optional[str] = Field(None, description="Error message if failed")

    model_config = {
        "json_schema_extra": {
            "example": {
                "verification_id": "550e8400-e29b-41d4-a716-446655440000",
                "status": "completed",
                "phone_number": "+15551234567",
                "sms_code": "123456",
                "sms_text": "Your verification code is: 123456",
                "sms_received_at": "2024-01-01T12:00:00Z",
                "service": "telegram",
                "country": "US",
                "cost": 2.00,
                "created_at": "2024-01-01T11:59:00Z",
                "completed_at": "2024-01-01T12:00:00Z",
                "expires_at": "2024-01-01T12:10:00Z",
                "activation_id": "tv_12345",
                "provider": "textverified",
                "retry_count": 0,
                "error_message": None,
            }
        }
    }


class VerificationRequestResponse(BaseModel):
    """Response after creating verification request."""

    success: bool = Field(..., description="Whether request was successful")
    verification_id: str = Field(..., description="Unique verification ID")
    phone_number: str = Field(..., description="Phone number for verification")
    service: str = Field(..., description="Service name")
    country: str = Field(..., description="Country code")
    cost: float = Field(..., description="Cost in USD")
    status: str = Field(..., description="Initial status")
    activation_id: str = Field(..., description="Provider activation ID")
    message: Optional[str] = Field(None, description="Additional message")

    model_config = {
        "json_schema_extra": {
            "example": {
                "success": True,
                "verification_id": "550e8400-e29b-41d4-a716-446655440000",
                "phone_number": "+15551234567",
                "service": "telegram",
                "country": "US",
                "cost": 2.00,
                "status": "pending",
                "activation_id": "tv_12345",
                "message": "Verification created successfully. SMS will arrive within 30 seconds.",
            }
        }
    }