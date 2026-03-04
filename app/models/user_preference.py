from sqlalchemy import Boolean, Column, Float, String

from app.models.base import BaseModel


class UserPreference(BaseModel):
    """User generic preferences and settings."""

    __tablename__ = "user_preferences"

    user_id = Column(String, nullable=False, unique=True, index=True)

    # Privacy Settings
    profile_visibility = Column(Boolean, default=False)
    analytics_tracking = Column(Boolean, default=True)
    data_retention = Column(String, default="90")  # '30', '90', '365', 'forever'
    language = Column(String, default="en")
    currency = Column(String, default="USD")

    # Billing Settings
    billing_email = Column(String, nullable=True)
    billing_address = Column(String, nullable=True)
    auto_recharge = Column(Boolean, default=False)
    recharge_amount = Column(Float, default=10.0)
    auto_recharge_threshold = Column(Float, default=5.0)
    spending_limit = Column(Float, nullable=True)
    low_balance_alert_threshold = Column(Float, nullable=True)

    # Payment Method (Paystack card on file)
    paystack_authorization_code = Column(String, nullable=True)
    card_last4 = Column(String, nullable=True)
    card_type = Column(String, nullable=True)
    card_expiry = Column(String, nullable=True)

    # Subscription
    subscription_renews_at = Column(String, nullable=True)  # ISO date string

    # Display Settings (Future proofing)
    theme = Column(String, default="light")