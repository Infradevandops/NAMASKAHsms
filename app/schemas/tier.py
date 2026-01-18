"""Tier response schemas for validation."""

from typing import Dict, List, Optional
from pydantic import BaseModel, Field, field_validator


class TierFeatures(BaseModel):
    """Tier features schema."""

    api_access: bool
    area_code_selection: bool
    isp_filtering: bool
    api_key_limit: int
    support_level: str


class TierInfo(BaseModel):
    """Single tier information schema."""

    tier: str = Field(..., description="Tier identifier (freemium, payg, pro, custom)")
    name: str = Field(..., description="Display name of the tier")
    price_monthly: float = Field(..., ge=0, description="Monthly price in dollars")
    price_display: str = Field(..., description="Formatted price display string")
    quota_usd: float = Field(..., ge=0, description="Monthly quota in USD")
    overage_rate: float = Field(..., ge=0, description="Overage rate per dollar")
    features: TierFeatures = Field(..., description="Tier features")

    @field_validator("tier")
    @classmethod
    def validate_tier(cls, v):
        """Validate tier is one of the allowed values."""
        allowed_tiers = {"freemium", "payg", "pro", "custom"}
        if v not in allowed_tiers:
            raise ValueError(f"Tier must be one of {allowed_tiers}")
        return v


class TiersListResponse(BaseModel):
    """Response schema for /api/tiers/ endpoint."""

    tiers: List[TierInfo] = Field(..., description="List of available tiers")

    @field_validator("tiers")
    @classmethod
    def validate_tiers_count(cls, v):
        """Validate that we have exactly 4 tiers."""
        if len(v) != 4:
            raise ValueError("Must have exactly 4 tiers")
        return v


class CurrentTierResponse(BaseModel):
    """Response schema for /api/tiers/current endpoint."""

    current_tier: str = Field(..., description="User's current tier")
    tier_name: str = Field(..., description="Display name of current tier")
    price_monthly: float = Field(..., ge=0, description="Monthly price in dollars")
    quota_usd: float = Field(..., ge=0, description="Monthly quota in USD")
    quota_used_usd: float = Field(..., ge=0, description="Quota used this month in USD")
    quota_remaining_usd: float = Field(..., ge=0, description="Remaining quota in USD")
    sms_count: int = Field(..., ge=0, description="SMS count this month")
    within_quota: bool = Field(..., description="Whether user is within quota")
    overage_rate: float = Field(..., ge=0, description="Overage rate per dollar")
    features: TierFeatures = Field(..., description="Tier features")

    @field_validator("current_tier")
    @classmethod
    def validate_tier(cls, v):
        """Validate tier is one of the allowed values."""
        allowed_tiers = {"freemium", "payg", "pro", "custom"}
        if v not in allowed_tiers:
            raise ValueError(f"Tier must be one of {allowed_tiers}")
        return v


class AnalyticsSummaryResponse(BaseModel):
    """Response schema for /api/analytics/summary endpoint."""

    total_verifications: int = Field(..., ge=0, description="Total verifications")
    successful_verifications: int = Field(..., ge=0, description="Successful verifications")
    failed_verifications: int = Field(..., ge=0, description="Failed verifications")
    pending_verifications: int = Field(..., ge=0, description="Pending verifications")
    success_rate: float = Field(..., ge=0, le=1, description="Success rate (0-1)")
    total_spent: float = Field(..., ge=0, description="Total amount spent")
    revenue: float = Field(..., ge=0, description="Revenue (backward compatibility)")
    average_cost: float = Field(..., ge=0, description="Average cost per verification")
    recent_activity: int = Field(..., ge=0, description="Recent activity count")
    monthly_verifications: int = Field(..., ge=0, description="Monthly verifications")
    monthly_spent: float = Field(..., ge=0, description="Monthly spending")
    last_updated: str = Field(..., description="Last update timestamp")


class DashboardActivity(BaseModel):
    """Single dashboard activity item schema."""

    id: str = Field(..., description="Activity ID")
    service_name: str = Field(..., description="Service name")
    phone_number: str = Field(..., description="Phone number")
    status: str = Field(..., description="Activity status")
    created_at: Optional[str] = Field(None, description="Creation timestamp")

    @field_validator("status")
    @classmethod
    def validate_status(cls, v):
        """Validate status is one of the allowed values."""
        allowed_statuses = {"pending", "completed", "failed", "expired", "processing"}
        if v not in allowed_statuses:
            raise ValueError(f"Status must be one of {allowed_statuses}")
        return v


# For list responses, we just use List[DashboardActivity] directly
DashboardActivityResponse = List[DashboardActivity]
