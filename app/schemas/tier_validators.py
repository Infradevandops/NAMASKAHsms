"""Response schema validators for tier-related API endpoints.

These validators ensure API responses contain all required fields
and have correct data types for frontend consumption.
"""

from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field, validator
from datetime import datetime


class TierFeaturesSchema(BaseModel):
    """Schema for tier features object."""

    api_access: bool
    area_code_selection: bool = Field(default=False)
    isp_filtering: bool = Field(default=False)
    api_key_limit: int = Field(default=0)
    support_level: str = Field(default="community")


class TierSchema(BaseModel):
    """Schema for a single tier in the list."""

    tier: str
    name: str
    price_monthly: float
    price_display: str
    quota_usd: float
    overage_rate: float
    features: TierFeaturesSchema


class TierListResponse(BaseModel):
    """Schema for /api/tiers/ response."""

    tiers: List[TierSchema]

    @validator("tiers")
    def validate_tiers_count(cls, v):
        """Ensure we have all 4 tiers."""
        if len(v) < 4:
            raise ValueError(f"Expected at least 4 tiers, got {len(v)}")
        return v


class CurrentTierFeaturesSchema(BaseModel):
    """Schema for current tier features."""

    api_access: bool
    area_code_selection: bool = Field(default=False)
    isp_filtering: bool = Field(default=False)
    api_key_limit: int = Field(default=0)
    support_level: str = Field(default="community")


class CurrentTierResponse(BaseModel):
    """Schema for /api/tiers/current response."""

    current_tier: str
    tier_name: str
    price_monthly: float
    quota_usd: float
    quota_used_usd: float
    quota_remaining_usd: float
    sms_count: int
    within_quota: bool
    overage_rate: float
    features: CurrentTierFeaturesSchema

    @validator("current_tier")
    def validate_tier_value(cls, v):
        """Ensure tier is a valid value."""
        valid_tiers = {"freemium", "payg", "pro", "custom"}
        if v not in valid_tiers:
            raise ValueError(f"Invalid tier: {v}. Must be one of {valid_tiers}")
        return v


class AnalyticsSummaryResponse(BaseModel):
    """Schema for /api/analytics/summary response."""

    total_verifications: int
    successful_verifications: int
    failed_verifications: int = Field(default=0)
    pending_verifications: int = Field(default=0)
    success_rate: float
    total_spent: float
    revenue: float = Field(default=0.0)  # Backward compatibility
    average_cost: float = Field(default=0.0)
    recent_activity: int = Field(default=0)
    monthly_verifications: int = Field(default=0)
    monthly_spent: float = Field(default=0.0)
    last_updated: str

    @validator("success_rate")
    def validate_success_rate(cls, v):
        """Ensure success rate is between 0 and 1."""
        if v < 0 or v > 1:
            raise ValueError(f"Success rate must be between 0 and 1, got {v}")
        return v


class ActivityItemSchema(BaseModel):
    """Schema for a single activity item."""

    id: str
    service_name: str
    phone_number: str
    status: str
    created_at: Optional[str] = None


class DashboardActivityResponse(BaseModel):
    """Schema for /api/dashboard/activity/recent response (list of activities)."""

    __root__: List[ActivityItemSchema]


def validate_tier_list_response(data: Dict[str, Any]) -> TierListResponse:
    """Validate /api/tiers/ response.

    Args:
        data: Response data from the API

    Returns:
        Validated TierListResponse

    Raises:
        ValueError: If validation fails
    """
    return TierListResponse(**data)


def validate_current_tier_response(data: Dict[str, Any]) -> CurrentTierResponse:
    """Validate /api/tiers/current response.

    Args:
        data: Response data from the API

    Returns:
        Validated CurrentTierResponse

    Raises:
        ValueError: If validation fails
    """
    return CurrentTierResponse(**data)


def validate_analytics_summary_response(data: Dict[str, Any]) -> AnalyticsSummaryResponse:
    """Validate /api/analytics/summary response.

    Args:
        data: Response data from the API

    Returns:
        Validated AnalyticsSummaryResponse

    Raises:
        ValueError: If validation fails
    """
    return AnalyticsSummaryResponse(**data)


def validate_dashboard_activity_response(data: List[Dict[str, Any]]) -> List[ActivityItemSchema]:
    """Validate /api/dashboard/activity/recent response.

    Args:
        data: Response data from the API (list of activities)

    Returns:
        List of validated ActivityItemSchema

    Raises:
        ValueError: If validation fails
    """
    return [ActivityItemSchema(**item) for item in data]


# Validation helper functions for frontend use
def get_validation_errors(data: Dict[str, Any], schema_type: str) -> List[str]:
    """Get list of validation errors for a response.

    Args:
        data: Response data to validate
        schema_type: One of 'tier_list', 'current_tier', 'analytics_summary', 'dashboard_activity'

    Returns:
        List of error messages (empty if valid)
    """
    errors = []

    try:
        if schema_type == "tier_list":
            validate_tier_list_response(data)
        elif schema_type == "current_tier":
            validate_current_tier_response(data)
        elif schema_type == "analytics_summary":
            validate_analytics_summary_response(data)
        elif schema_type == "dashboard_activity":
            validate_dashboard_activity_response(data)
        else:
            errors.append(f"Unknown schema type: {schema_type}")
    except Exception as e:
        errors.append(str(e))

    return errors


def is_valid_response(data: Any, schema_type: str) -> bool:
    """Check if a response is valid.

    Args:
        data: Response data to validate
        schema_type: One of 'tier_list', 'current_tier', 'analytics_summary', 'dashboard_activity'

    Returns:
        True if valid, False otherwise
    """
    return len(get_validation_errors(data, schema_type)) == 0
