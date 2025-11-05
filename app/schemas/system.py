"""System schemas for support tickets and admin operations."""
from typing import Optional
from datetime import datetime
from pydantic import BaseModel


class SupportTicketResponse(BaseModel):
    """Support ticket response schema."""
    id: str
    name: str
    email: str
    category: str
    message: str
    status: str
    admin_response: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True