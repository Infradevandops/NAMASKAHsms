"""System schemas for health checks and monitoring."""
from typing import Any, Dict, Optional

from pydantic import BaseModel


class ServiceStatus(BaseModel):
    name: str
    status: str
    response_time: Optional[float] = None
    details: Optional[Dict[str, Any]] = None


class ServiceStatusSummary(BaseModel):
    overall_status: str
    services: Dict[str, ServiceStatus]
    timestamp: str


class SupportTicketResponse(BaseModel):
    id: str
    name: str
    email: str
    category: str
    message: str
    status: str
    admin_response: Optional[str] = None
    created_at: str
    updated_at: Optional[str] = None

    class Config:
        from_attributes = True
