"""Tier response schemas for validation."""

from typing import List, Optional
from app.core.pydantic_compat import BaseModel, Field, field_validator


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


class TierListResponse(BaseModel):
    """Response schema for tier list endpoint."""

    tiers: List[TierInfo] = Field(..., description="List of available tiers")
    current_tier: str = Field(..., description="User's current tier")
    can_upgrade: bool = Field(..., description="Whether user can upgrade")
    can_downgrade: bool = Field(..., description="Whether user can downgrade")

    @field_validator("tiers")
    @classmethod
    def validate_tiers_count(cls, v):
        """Ensure we have all 4 tiers."""
        if len(v) < 4:
            raise ValueError(f"Expected at least 4 tiers, got {len(v)}")
        return v


class CurrentTierFeaturesSchema(BaseModel):
    """Schema for current tier features response."""

    tier: str = Field(..., description="Current tier name")
    features: TierFeatures = Field(..., description="Current tier features")
    usage: dict = Field(..., description="Current usage statistics")
    limits: dict = Field(..., description="Current tier limits")


class TierUpgradeRequest(BaseModel):
    """Schema for tier upgrade requests."""

    target_tier: str = Field(..., description="Target tier to upgrade to")
    payment_method: Optional[str] = Field(
        default="paystack", description="Payment method"
    )

    @field_validator("target_tier")
    @classmethod
    def validate_tier_value(cls, v):
        """Validate target tier is upgradeable."""
        allowed_tiers = {"payg", "pro", "custom"}
        if v not in allowed_tiers:
            raise ValueError(f"Can only upgrade to: {allowed_tiers}")
        return v


class TierUpgradeResponse(BaseModel):
    """Schema for tier upgrade response."""

    success: bool = Field(..., description="Whether upgrade was successful")
    new_tier: str = Field(..., description="New tier after upgrade")
    payment_url: Optional[str] = Field(
        None, description="Payment URL if payment required"
    )
    message: str = Field(..., description="Success or error message")
