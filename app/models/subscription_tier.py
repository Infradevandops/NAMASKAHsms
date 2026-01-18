"""Subscription tier model for multi-tier SaaS platform."""

from sqlalchemy import Boolean, Column, String, Integer, JSON, Float
from enum import Enum as PyEnum

from app.models.base import BaseModel


class TierEnum(str, PyEnum):
    """Subscription tier levels."""

    FREEMIUM = "freemium"
    PAYG = "payg"
    PRO = "pro"
    CUSTOM = "custom"


class SubscriptionTier(BaseModel):
    """Subscription tier configuration and limits."""

    __tablename__ = "subscription_tiers"

    # Tier identification
    tier = Column(String(20), unique=True, nullable=False, index=True)  # freemium, starter, turbo
    name = Column(String(50), nullable=False)  # Display name
    description = Column(String(500))

    # Pricing
    price_monthly = Column(Integer, default=0, nullable=False)  # Price in cents (0 for freemium)
    payment_required = Column(Boolean, default=False, nullable=False)  # True for paid tiers
    quota_usd = Column(Float, default=0.0)
    overage_rate = Column(Float, default=0.0)

    # Feature flags
    has_api_access = Column(Boolean, default=False, nullable=False)
    has_area_code_selection = Column(Boolean, default=False, nullable=False)
    has_isp_filtering = Column(Boolean, default=False, nullable=False)

    # Limits
    api_key_limit = Column(Integer, default=0, nullable=False)  # 0 = no API, -1 = unlimited
    daily_verification_limit = Column(Integer, default=100, nullable=False)
    monthly_verification_limit = Column(Integer, default=3000, nullable=False)
    country_limit = Column(Integer, default=5, nullable=False)  # -1 = all countries
    sms_retention_days = Column(Integer, default=1, nullable=False)

    # Support level
    support_level = Column(String(20), default="community")  # community, email, priority

    # Additional features (JSON for flexibility)
    features = Column(JSON, default=dict)  # {"webhooks": true, "custom_branding": false, etc}

    # Rate limiting
    rate_limit_per_minute = Column(Integer, default=10, nullable=False)
    rate_limit_per_hour = Column(Integer, default=100, nullable=False)
