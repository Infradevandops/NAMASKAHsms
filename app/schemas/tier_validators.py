"""Response schema validators for tier-related API endpoints.

These validators ensure API responses contain all required fields
and have correct data types for frontend consumption.
"""

from typing import Any, Dict, List, Optional
from app.core.pydantic_compat import BaseModel, Field, field_validator


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

    @field_validator("tier")
    @classmethod
    def validate_tier_name(cls, v):
        """Validate tier name is allowed."""
        allowed = {"freemium", "payg", "pro", "custom"}
        if v not in allowed:
            raise ValueError(f"Tier must be one of {allowed}")
        return v


class TierListResponseSchema(BaseModel):
        """Schema for tier list API response."""

        tiers: List[TierSchema]
        current_tier: str
        can_upgrade: bool = Field(default=True)
        can_downgrade: bool = Field(default=False)

        @field_validator("tiers")
        @classmethod
    def validate_tiers_count(cls, v):
        """Ensure we have all 4 tiers."""
        if len(v) < 4:
            raise ValueError(f"Expected at least 4 tiers, got {len(v)}")
        return v


class CurrentTierFeaturesSchema(BaseModel):
        """Schema for current tier features response."""

        tier: str
        features: TierFeaturesSchema
        usage: Dict[str, Any] = Field(default_factory=dict)
        limits: Dict[str, Any] = Field(default_factory=dict)

        @field_validator("tier")
        @classmethod
    def validate_tier_value(cls, v):
        """Validate current tier value."""
        allowed = {"freemium", "payg", "pro", "custom"}
        if v not in allowed:
            raise ValueError(f"Current tier must be one of {allowed}")
        return v


class TierUpgradeRequestSchema(BaseModel):
        """Schema for tier upgrade request."""

        target_tier: str
        payment_method: str = Field(default="paystack")

        @field_validator("target_tier")
        @classmethod
    def validate_upgrade_tier(cls, v):
        """Validate upgrade target tier."""
        allowed = {"payg", "pro", "custom"}
        if v not in allowed:
            raise ValueError(f"Can only upgrade to: {allowed}")
        return v


class TierUpgradeResponseSchema(BaseModel):
        """Schema for tier upgrade response."""

        success: bool
        new_tier: str
        payment_url: Optional[str] = None
        message: str

        @field_validator("new_tier")
        @classmethod
    def validate_new_tier(cls, v):
        """Validate new tier after upgrade."""
        allowed = {"freemium", "payg", "pro", "custom"}
        if v not in allowed:
            raise ValueError(f"New tier must be one of {allowed}")
        return v
