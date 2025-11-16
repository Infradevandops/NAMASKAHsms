"""Rental schemas for validation."""
from datetime import datetime
from decimal import Decimal
from typing import List, Optional

from pydantic import BaseModel, Field


class RentalCreate(BaseModel):
    service_name: Optional[str] = Field(None, min_length=1, max_length=50)
    country_code: str = Field(..., min_length=2, max_length=3)
    duration_hours: int = Field(default=24, ge=1, le=720)  # 1 hour to 1 month
    operator: Optional[str] = Field(default="any", description="Network operator")
    auto_extend: bool = Field(default=False, description="Auto-extend rental before expiry")


class RentalExtend(BaseModel):
    additional_hours: int = Field(..., ge=1, le=168)


class RentalResponse(BaseModel):
    id: str
    phone_number: str
    service_name: str
    country_code: str
    expires_at: datetime
    status: str
    time_remaining_seconds: int
    cost: Decimal
    duration_hours: int
    auto_extend: bool
    renewal_fee: Decimal
    activation_id: str

    class Config:
        from_attributes = True


class RentalMessage(BaseModel):
    message: str
    received_at: datetime


class RentalMessagesResponse(BaseModel):
    phone_number: str
    service_name: str
    message_count: int
    messages: List[str]
