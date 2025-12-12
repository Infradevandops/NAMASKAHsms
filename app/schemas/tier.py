"""Pydantic schemas for tier and subscription management."""
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime


class TierInfo(BaseModel):
    """Information about a subscription tier."""
    name: str
    tier: str
    price_monthly: int  # in cents
    price_display: str  # e.g., "$9/mo"
    payment_required: bool
    has_api_access: bool
    has_area_code_selection: bool
    has_isp_filtering: bool
    api_key_limit: int
    daily_verification_limit: int
    monthly_verification_limit: int
    country_limit: int
    sms_retention_days: int
    support_level: str
    features: Dict[str, bool]


class UserTierInfo(BaseModel):
    """User's current tier information."""
    current_tier: str
    tier_name: str
    upgraded_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    days_remaining: Optional[int] = None
    can_upgrade: bool = True
    upgrade_options: list[str] = []


class TierUpgradeRequest(BaseModel):
    """Request to upgrade to a new tier."""
    target_tier: str = Field(..., pattern="^(starter|turbo)$")
    payment_method_id: Optional[str] = None  # Stripe payment method ID


class TierUpgradeResponse(BaseModel):
    """Response after tier upgrade."""
    success: bool
    message: str
    new_tier: str
    expires_at: Optional[datetime] = None
    payment_required: bool
    amount_charged: Optional[int] = None  # in cents


class APIKeyCreate(BaseModel):
    """Request to create a new API key."""
    name: str = Field(..., min_length=1, max_length=100)


class APIKeyResponse(BaseModel):
    """API key response (only shown once)."""
    id: str
    name: str
    key: str  # Only returned on creation
    key_preview: str
    created_at: datetime
    expires_at: Optional[datetime] = None


class APIKeyInfo(BaseModel):
    """API key information (without the actual key)."""
    id: str
    name: str
    key_preview: str
    is_active: bool
    request_count: int
    last_used: Optional[datetime] = None
    created_at: datetime
    expires_at: Optional[datetime] = None


class APIKeyUsageStats(BaseModel):
    """Usage statistics for an API key."""
    key_id: str
    name: str
    total_requests: int
    requests_today: int
    requests_this_month: int
    last_used: Optional[datetime] = None
    created_at: datetime
