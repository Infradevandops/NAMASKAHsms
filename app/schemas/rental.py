"""Rental schemas for validation."""

from datetime import datetime
from decimal import Decimal
from typing import List

from pydantic import BaseModel, Field


class RentalCreate(BaseModel):
    service_name: str = Field(..., min_length=1, max_length=50)
    country_code: str = Field(..., min_length=2, max_length=3)
    duration_hours: int = Field(default=24, ge=1, le=168)  # 1 hour to 1 week


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
