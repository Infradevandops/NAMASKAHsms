"""User - related database models."""
from sqlalchemy import Boolean, Column, DateTime, Float, String
from sqlalchemy.orm import relationship

from app.models.base import BaseModel


class User(BaseModel):
    """User account model."""

    __tablename__ = "users"

    email = Column(String, unique=True, nullable=False, index=True)
    password_hash = Column(String, nullable=True)  # Nullable for OAuth users
    credits = Column(Float, default=0.0, nullable=False)
    free_verifications = Column(Float, default=1.0, nullable=False)
    is_admin = Column(Boolean, default=False, nullable=False)
    is_moderator = Column(Boolean, default=False, nullable=False)
    email_verified = Column(Boolean, default=False, nullable=False)
    verification_token = Column(String)
    reset_token = Column(String)
    reset_token_expires = Column(DateTime)
    
    # Subscription tier (Task: Versioning)
    subscription_tier = Column(String(20), default="freemium", nullable=False, index=True)
    tier_upgraded_at = Column(DateTime)  # When user last upgraded
    tier_expires_at = Column(DateTime)  # For subscription expiration
    
    # Pricing enforcement fields
    bonus_sms_balance = Column(Float, default=0.0, nullable=False)  # Freemium bonus SMS
    monthly_quota_used = Column(Float, default=0.0, nullable=False)  # Current month usage
    monthly_quota_reset_date = Column(DateTime, nullable=True)  # Last reset date
    
    referral_code = Column(String, unique=True, index=True)
    referred_by = Column(String)
    referral_earnings = Column(Float, default=0.0, nullable=False)

    # Google OAuth fields
    google_id = Column(String(255), nullable=True, index=True)
    provider = Column(String(50), default="email", nullable=False)
    avatar_url = Column(String(500), nullable=True)

    # Token management fields (Task 1.2)
    refresh_token = Column(String, nullable=True, unique=True, index=True)
    refresh_token_expires = Column(DateTime, nullable=True)
    last_login = Column(DateTime, nullable=True)

    # User preferences (language/currency)
    language = Column(String(10), default="en", nullable=False)
    currency = Column(String(10), default="USD", nullable=False)

    # Affiliate fields
    affiliate_id = Column(String(50), nullable=True)
    partner_type = Column(String(50), nullable=True)
    commission_tier = Column(String(50), nullable=True)
    is_affiliate = Column(Boolean, default=False, nullable=False)

    # Admin management fields
    tier_id = Column(String(50), default="freemium", nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    is_suspended = Column(Boolean, default=False, nullable=False)
    suspended_at = Column(DateTime, nullable=True)
    suspension_reason = Column(String(500), nullable=True)
    is_banned = Column(Boolean, default=False, nullable=False)
    banned_at = Column(DateTime, nullable=True)
    ban_reason = Column(String(500), nullable=True)
    is_deleted = Column(Boolean, default=False, nullable=False)
    deleted_at = Column(DateTime, nullable=True)
    deletion_reason = Column(String(500), nullable=True)

    # Relationships
    notifications = relationship("Notification", back_populates="user")
    balance_transactions = relationship("BalanceTransaction", back_populates="user")
    commissions = relationship("AffiliateCommission", back_populates="affiliate")
    enterprise_account = relationship("EnterpriseAccount",
                                      back_populates="user", uselist=False)
    revenue_shares = relationship("RevenueShare", back_populates="partner")
    payout_requests = relationship("PayoutRequest", back_populates="affiliate")
    reseller_account = relationship("ResellerAccount",
                                    back_populates="user", uselist=False)
    partner_features = relationship("PartnerFeature", back_populates="partner")


# APIKey is defined in app/models/api_key.py to avoid duplication


class Webhook(BaseModel):
    """Webhook configuration for notifications."""

    __tablename__ = "webhooks"

    user_id = Column(String, nullable=False, index=True)
    url = Column(String, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)


class NotificationSettings(BaseModel):
    """User notification preferences."""

    __tablename__ = "notification_settings"

    user_id = Column(String, unique=True, nullable=False, index=True)
    email_on_sms = Column(Boolean, default=True, nullable=False)
    email_on_low_balance = Column(Boolean, default=True, nullable=False)
    low_balance_threshold = Column(Float, default=1.0, nullable=False)


class Referral(BaseModel):
    """Referral tracking."""

    __tablename__ = "referrals"

    referrer_id = Column(String, nullable=False, index=True)
    referred_id = Column(String, nullable=False, index=True)
    reward_amount = Column(Float, default=1.0, nullable=False)


class Subscription(BaseModel):
    """User subscription plans."""

    __tablename__ = "subscriptions"

    user_id = Column(String, unique=True, nullable=False, index=True)
    plan = Column(String, nullable=False)
    status = Column(String, default="active", nullable=False)
    price = Column(Float, nullable=False)
    discount = Column(Float, default=0.0, nullable=False)
    duration = Column(Float, default=0, nullable=False)
    expires_at = Column(DateTime)
    cancelled_at = Column(DateTime)


class NotificationPreferences(BaseModel):
    """Enhanced notification preferences."""

    __tablename__ = "notification_preferences"

    user_id = Column(String, unique=True, nullable=False, index=True)
    in_app_notifications = Column(Boolean, default=True, nullable=False)
    email_notifications = Column(Boolean, default=True, nullable=False)
    receipt_notifications = Column(Boolean, default=True, nullable=False)

# InAppNotification is defined in system.py to avoid duplication
