"""Subscription add-on model — Sprint C-009.

Tracks optional paid add-ons for users (e.g. API access for PAYG tier).
Each user can have at most one active record per addon_type (UNIQUE constraint).
"""

from sqlalchemy import Boolean, Column, DateTime, Numeric, String, UniqueConstraint

from app.models.base import BaseModel


class SubscriptionAddon(BaseModel):
    """Optional paid add-on attached to a user's subscription."""

    __tablename__ = "subscription_addons"

    user_id = Column(String, nullable=False, index=True)
    addon_type = Column(String(50), nullable=False)  # e.g. 'api_access'
    price_usd = Column(Numeric(10, 2), nullable=False)
    active = Column(Boolean, nullable=False, default=True)
    started_at = Column(DateTime, nullable=False)
    expires_at = Column(DateTime, nullable=True)
    paystack_subscription_code = Column(String(100), nullable=True)

    __table_args__ = (
        UniqueConstraint("user_id", "addon_type", name="uq_user_addon_type"),
    )

    def __repr__(self) -> str:
        return f"<SubscriptionAddon user={self.user_id} type={self.addon_type} active={self.active}>"
