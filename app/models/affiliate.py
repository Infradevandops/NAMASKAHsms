"""Affiliate program models."""

from sqlalchemy import JSON, Boolean, Column, DateTime, Float, ForeignKey, String, Text
from sqlalchemy.orm import relationship

from app.models.base import BaseModel


class AffiliateProgram(BaseModel):

    __tablename__ = "affiliate_programs"

    name = Column(String(100), nullable=False)
    program_type = Column(String(50), nullable=False)  # 'referral' or 'enterprise'
    commission_rate = Column(Float, nullable=False)
    tier_requirements = Column(JSON, default=lambda: {})
    features = Column(JSON, default=lambda: {})
    is_active = Column(Boolean, default=True)


class AffiliateApplication(BaseModel):

    __tablename__ = "affiliate_applications"

    email = Column(String(255), nullable=False)
    program_type = Column(String(50), nullable=False)
    program_options = Column(JSON, default=lambda: {})
    message = Column(Text, nullable=True)
    status = Column(String(50), default="pending")
    admin_notes = Column(Text, nullable=True)


class AffiliateCommission(BaseModel):

    __tablename__ = "affiliate_commissions"

    affiliate_id = Column(String, ForeignKey("users.id"), nullable=False)
    transaction_id = Column(String(255), nullable=False)
    amount = Column(Float, nullable=False)
    commission_rate = Column(Float, nullable=False)
    status = Column(String(50), default="pending")
    payout_date = Column(DateTime, nullable=True)

    # Relationships
    affiliate = relationship("User", back_populates="commissions")