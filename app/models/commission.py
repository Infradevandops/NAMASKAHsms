"""Commission and revenue sharing models."""

from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
)
from sqlalchemy.orm import relationship

from app.models.base import BaseModel


class CommissionTier(BaseModel):

    __tablename__ = "commission_tiers"

    name = Column(String(50), nullable=False, unique=True)
    base_rate = Column(Float, nullable=False)
    bonus_rate = Column(Float, default=0.0)
    min_volume = Column(Float, default=0.0)
    min_referrals = Column(Integer, default=0)
    requirements = Column(JSON, default=lambda: {})
    benefits = Column(JSON, default=lambda: {})
    is_active = Column(Boolean, default=True)


class RevenueShare(BaseModel):

    __tablename__ = "revenue_shares"

    partner_id = Column(UUID(as_uuid=False), ForeignKey("users.id"), nullable=False)
    transaction_id = Column(String(255), nullable=False)
    revenue_amount = Column(Float, nullable=False)
    commission_rate = Column(Float, nullable=False)
    commission_amount = Column(Float, nullable=False)
    tier_name = Column(String(50), nullable=False)
    attribution_type = Column(String(50), default="last_touch")
    status = Column(String(50), default="pending")
    processed_at = Column(DateTime, nullable=True)

    # Relationships
    partner = relationship("User", back_populates="revenue_shares")


class PayoutRequest(BaseModel):

    __tablename__ = "payout_requests"

    affiliate_id = Column(UUID(as_uuid=False), ForeignKey("users.id"), nullable=False)
    amount = Column(Float, nullable=False)
    currency = Column(String(3), default="NGN")
    payment_method = Column(String(50), nullable=False)
    payment_details = Column(JSON, default=lambda: {})
    status = Column(String(50), default="pending")
    processed_at = Column(DateTime, nullable=True)
    transaction_reference = Column(String(255), nullable=True)
    admin_notes = Column(String(500), nullable=True)

    # Relationships
    affiliate = relationship("User", back_populates="payout_requests")