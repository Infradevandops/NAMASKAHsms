"""Activity schemas for API responses."""

from datetime import datetime
from typing import Any, Dict, Optional
from app.core.pydantic_compat import BaseModel


class ActivityResponse(BaseModel):
    """Schema for activity response."""
    
    id: str
    resource_type: str
    resource_id: Optional[str] = None
    action: str
    status: str
    details: Optional[Dict[str, Any]] = None
    created_at: datetime
    
    model_config = {"from_attributes": True}


class ActivityCreate(BaseModel):
    """Schema for creating an activity."""
    
    resource_type: str
    resource_id: Optional[str] = None
    action: str
    status: str = "pending"
    details: Optional[Dict[str, Any]] = None


class ActivitySummary(BaseModel):
    """Schema for activity summary."""
    
    total_activities: int
    by_resource_type: Dict[str, int]
    by_status: Dict[str, int]
    recent_count: int
