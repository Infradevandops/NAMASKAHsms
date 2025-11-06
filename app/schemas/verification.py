"""Verification request/response schemas."""

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field, validator


class VerificationCreate(BaseModel):
    """Schema for creating SMS/voice verification."""

    service_name: str = Field(
        ..., min_length=1, description="Service name (e.g., telegram, whatsapp)"
    )
    country: str = Field(default="US", description="Country code for verification")
    capability: str = Field(
        default="sms", description="Verification type: sms or voice"
    )
    area_code: Optional[str] = Field(None, description="Preferred area code (+$4)")
    carrier: Optional[str] = Field(None, description="Preferred carrier (+$6)")

    @validator("capability")
    def validate_capability(cls, v):
        if v not in ["sms", "voice"]:
            raise ValueError("Capability must be sms or voice")
        return v

    @validator("country")
    def validate_country(cls, v):
        if not v or len(v) != 2:
            raise ValueError("Country must be a 2-letter code")
        return v.upper()

    @validator("service_name")
    def validate_service_name(cls, v):
        # Basic service name validation
        if not v or len(v.strip()) == 0:
            raise ValueError("Service name cannot be empty")
        return v.lower().strip()

    model_config = {
        "json_schema_extra": {
            "example": {
                "service_name": "telegram",
                "country": "US",
                "capability": "sms",
                "area_code": "212",
                "carrier": "verizon",
            }
        }
    }


class VerificationResponse(BaseModel):
    """Schema for verification response."""

    id: str
    service_name: str
    phone_number: Optional[str]
    capability: str
    status: str
    cost: float
    requested_carrier: Optional[str]
    requested_area_code: Optional[str]
    created_at: datetime
    completed_at: Optional[datetime]

    model_config = {
        "from_attributes": True,
        "json_schema_extra": {
            "example": {
                "id": "verification_1642680000000",
                "service_name": "telegram",
                "phone_number": "+1234567890",
                "capability": "sms",
                "status": "pending",
                "cost": 1.0,
                "requested_carrier": "verizon",
                "requested_area_code": "212",
                "created_at": "2024-01-20T10:00:00Z",
                "completed_at": None,
            }
        },
    }


class MessageResponse(BaseModel):
    """Schema for SMS messages response."""

    verification_id: str
    messages: List[str] = Field(..., description="List of SMS messages received")

    model_config = {
        "json_schema_extra": {
            "example": {
                "verification_id": "verification_1642680000000",
                "messages": [
                    "Your verification code is: 123456",
                    "Code expires in 10 minutes",
                ],
            }
        }
    }


class NumberRentalRequest(BaseModel):
    """Schema for number rental request."""

    service_name: Optional[str] = Field(
        None, description="Service for rental (optional)"
    )
    duration_hours: float = Field(..., gt=0, description="Rental duration in hours")
    mode: str = Field(
        default="always_ready", description="Rental mode: always_ready or manual"
    )
    auto_extend: bool = Field(default=False, description="Auto-extend rental")
    area_code: Optional[str] = Field(None, description="Preferred area code")
    carrier: Optional[str] = Field(None, description="Preferred carrier")

    @validator("mode")
    def validate_mode(cls, v):
        if v not in ["always_ready", "manual"]:
            raise ValueError("Mode must be always_ready or manual")
        return v

    @validator("duration_hours")
    def validate_duration(cls, v):
        if v <= 0:
            raise ValueError("Duration must be positive")
        if v > 8760:  # 1 year
            raise ValueError("Maximum rental duration is 1 year")
        return v

    model_config = {
        "json_schema_extra": {
            "example": {
                "service_name": "telegram",
                "duration_hours": 24.0,
                "mode": "always_ready",
                "auto_extend": False,
                "area_code": "212",
                "carrier": "verizon",
            }
        }
    }


class NumberRentalResponse(BaseModel):
    """Schema for number rental response."""

    id: str
    phone_number: str
    service_name: Optional[str]
    duration_hours: float
    cost: float
    mode: str
    status: str
    started_at: datetime
    expires_at: datetime
    auto_extend: bool

    model_config = {
        "from_attributes": True,
        "json_schema_extra": {
            "example": {
                "id": "rental_1642680000000",
                "phone_number": "+1234567890",
                "service_name": "telegram",
                "duration_hours": 24.0,
                "cost": 12.0,
                "mode": "always_ready",
                "status": "active",
                "started_at": "2024-01-20T10:00:00Z",
                "expires_at": "2024-01-21T10:00:00Z",
                "auto_extend": False,
            }
        },
    }


class ExtendRentalRequest(BaseModel):
    """Schema for extending rental duration."""

    additional_hours: float = Field(..., gt=0, description="Additional hours to extend")

    @validator("additional_hours")
    def validate_additional_hours(cls, v):
        if v <= 0:
            raise ValueError("Additional hours must be positive")
        if v > 8760:  # 1 year
            raise ValueError("Maximum extension is 1 year")
        return v

    model_config = {"json_schema_extra": {"example": {"additional_hours": 12.0}}}


class RetryVerificationRequest(BaseModel):
    """Schema for retrying verification."""

    retry_type: str = Field(..., description="Retry type: voice, same, or new")

    @validator("retry_type")
    def validate_retry_type(cls, v):
        if v not in ["voice", "same", "new"]:
            raise ValueError("Retry type must be voice, same, or new")
        return v

    model_config = {"json_schema_extra": {"example": {"retry_type": "voice"}}}


class ServicePriceResponse(BaseModel):
    """Schema for service pricing information."""

    service_name: str
    tier: str
    base_price: float
    base_price_usd: float
    voice_premium: float
    user_plan: str
    monthly_verifications: int
    addons: dict

    model_config = {
        "json_schema_extra": {
            "example": {
                "service_name": "telegram",
                "tier": "popular",
                "base_price": 1.0,
                "base_price_usd": 2.0,
                "voice_premium": 0.25,
                "user_plan": "starter",
                "monthly_verifications": 5,
                "addons": {
                    "custom_area_code": 4.0,
                    "guaranteed_carrier": 6.0,
                    "priority_queue": 2.0,
                },
            }
        }
    }


class VerificationHistoryResponse(BaseModel):
    """Schema for verification history."""

    verifications: List[VerificationResponse]
    total_count: int

    model_config = {
        "json_schema_extra": {
            "example": {
                "verifications": [
                    {
                        "id": "verification_1642680000000",
                        "service_name": "telegram",
                        "phone_number": "+1234567890",
                        "capability": "sms",
                        "status": "completed",
                        "cost": 1.0,
                        "created_at": "2024-01-20T10:00:00Z",
                        "completed_at": "2024-01-20T10:05:00Z",
                    }
                ],
                "total_count": 1,
            }
        }
    }
