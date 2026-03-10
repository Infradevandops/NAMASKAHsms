"""Pricing tier and subscription models."""

from sqlalchemy import JSON, Boolean, Column, DateTime, Float, Integer, String

from app.models.base import BaseModel


class PricingTier(BaseModel):
    """Pricing tier model."""

    __tablename__ = "pricing_tiers"

    name = Column(
        String, unique=True, nullable=False, index=True
    )  # BASIC, STANDARD, PREMIUM, ENTERPRISE
    display_name = Column(String, nullable=False)  # "Basic", "Standard", etc
    description = Column(String)
    monthly_price = Column(Float, default=0.0, nullable=False)
    max_verifications_per_day = Column(Integer, default=-1)  # -1 for unlimited
    priority_number_access = Column(Float, default=0.0)  # 0%, 10%, 50%, 100%
    expedited_delivery_available = Column(Boolean, default=False)
    ultra_fast_delivery_available = Column(Boolean, default=False)
    api_rate_limit = Column(Integer, default=10)  # requests per minute
    support_level = Column(
        String, default="email"
    )  # email, priority_email, phone, dedicated
    bulk_operations_limit = Column(
        Integer, default=0
    )  # 0 for no bulk, -1 for unlimited
    webhook_support = Column(Boolean, default=False)
    analytics_level = Column(String, default="basic")  # basic, advanced, custom
    sla_uptime = Column(Float, default=99.0)  # 99.0, 99.5, 99.9, 99.99
    features = Column(JSON, default={})  # List of features
    is_active = Column(Boolean, default=True, nullable=False)
    display_order = Column(Integer, default=0)  # For sorting on UI


class UserSubscription(BaseModel):
    """User subscription model."""

    __tablename__ = "user_subscriptions"

    user_id = Column(String, unique=True, nullable=False, index=True)
    tier_id = Column(String, nullable=False)  # Reference to PricingTier.id
    tier_name = Column(String, nullable=False)  # BASIC, STANDARD, PREMIUM, ENTERPRISE
    monthly_price = Column(Float, default=0.0, nullable=False)
    status = Column(
        String, default="active", nullable=False
    )  # active, paused, cancelled
    started_at = Column(DateTime, nullable=True)
    expires_at = Column(DateTime, nullable=True)
    auto_renew = Column(Boolean, default=True, nullable=False)
    payment_method = Column(String, nullable=True)  # paystack, stripe, etc
    next_billing_date = Column(DateTime, nullable=True)
    cancelled_at = Column(DateTime, nullable=True)
    cancellation_reason = Column(String, nullable=True)


class ServiceAddOn(BaseModel):
    """Service add-on model."""

    __tablename__ = "service_addons"

    name = Column(
        String, unique=True, nullable=False, index=True
    )  # priority_numbers, expedited_delivery, etc
    display_name = Column(String, nullable=False)
    description = Column(String)
    base_cost = Column(
        Float, default=0.0, nullable=False
    )  # per verification or per month
    cost_type = Column(
        String, nullable=False
    )  # per_verification, per_month, per_number
    tier_availability = Column(
        JSON, default=[]
    )  # Which tiers can access: ["STANDARD", "PREMIUM", "ENTERPRISE"]
    is_active = Column(Boolean, default=True, nullable=False)
    display_order = Column(Integer, default=0)


class UserAddOnSubscription(BaseModel):
    """User add-on subscription model."""

    __tablename__ = "user_addon_subscriptions"

    user_id = Column(String, nullable=False, index=True)
    addon_id = Column(String, nullable=False)
    addon_name = Column(String, nullable=False)
    status = Column(
        String, default="active", nullable=False
    )  # active, paused, cancelled
    started_at = Column(DateTime, nullable=True)
    expires_at = Column(DateTime, nullable=True)
    auto_renew = Column(Boolean, default=True, nullable=False)
    cost = Column(Float, default=0.0, nullable=False)
    cost_type = Column(
        String, nullable=False
    )  # per_verification, per_month, per_number
    next_billing_date = Column(DateTime, nullable=True)
    cancelled_at = Column(DateTime, nullable=True)


class VerificationPricing(BaseModel):
    """Verification pricing by service and country."""

    __tablename__ = "verification_pricing"

    service_name = Column(String, nullable=False, index=True)
    country_code = Column(String, nullable=False, index=True)
    base_price = Column(Float, default=0.10, nullable=False)  # Base price in USD
    priority_surcharge = Column(Float, default=0.50, nullable=False)  # Priority add-on
    ultra_fast_surcharge = Column(
        Float, default=1.00, nullable=False
    )  # Ultra-fast add-on
    is_active = Column(Boolean, default=True, nullable=False)
    last_updated = Column(DateTime, nullable=True)
