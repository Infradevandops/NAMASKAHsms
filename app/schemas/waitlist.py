"""Waitlist schemas for validation."""


from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr

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

    model_config = {"from_attributes": True}