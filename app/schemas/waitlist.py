"""Waitlist schemas for validation."""
from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime


class WaitlistJoin(BaseModel):
    email: EmailStr
    name: Optional[str] = None
    source: Optional[str] = "landing_page"


class WaitlistResponse(BaseModel):
    id: int
    email: str
    name: Optional[str]
    is_notified: bool
    source: str
    created_at: datetime

    class Config:
        from_attributes = True
