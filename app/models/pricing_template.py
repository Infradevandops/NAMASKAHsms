"""Pricing Template Models"""

from sqlalchemy import (
from sqlalchemy.dialects.postgresql import JSONB as PostgresJSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base

    DECIMAL,
    JSON,
    TIMESTAMP,
    Boolean,
    Column,
    ForeignKey,
    Integer,
    String,
    Text,
)


# Use cross-dialect JSONB (Postgres) / JSON (SQLite)
JSONB = JSON().with_variant(PostgresJSONB, "postgresql")


class PricingTemplate(Base):

    """Pricing template for managing multiple pricing strategies"""

    __tablename__ = "pricing_templates"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, unique=True)
    description = Column(Text)
    is_active = Column(Boolean, default=False, index=True)
    region = Column(String(10), default="US", index=True)
    currency = Column(String(3), default="USD")
    created_at = Column(TIMESTAMP, server_default=func.now())
    created_by = Column(String, ForeignKey("users.id", ondelete="SET NULL"))
    effective_date = Column(TIMESTAMP)
    expires_at = Column(TIMESTAMP)
    template_metadata = Column(JSONB)  # For A/B testing, notes, etc.

    # Relationships
    tiers = relationship("TierPricing", back_populates="template", cascade="all, delete-orphan")
    history = relationship("PricingHistory", back_populates="template")
    creator = relationship("User", foreign_keys=[created_by])

def __repr__(self):

        return f"<PricingTemplate(name='{self.name}', active={self.is_active}, region='{self.region}')>"


class TierPricing(Base):

    """Tier pricing details for a template"""

    __tablename__ = "tier_pricing"

    id = Column(Integer, primary_key=True, index=True)
    template_id = Column(Integer, ForeignKey("pricing_templates.id", ondelete="CASCADE"), nullable=False)
    tier_name = Column(String(50), nullable=False)
    monthly_price = Column(DECIMAL(10, 2))
    included_quota = Column(DECIMAL(10, 2))
    overage_rate = Column(DECIMAL(10, 2))
    features = Column(JSONB)
    api_keys_limit = Column(Integer)
    display_order = Column(Integer)

    # Relationships
    template = relationship("PricingTemplate", back_populates="tiers")

def __repr__(self):

        return f"<TierPricing(tier='{self.tier_name}', price={self.monthly_price})>"


class PricingHistory(Base):

    """Audit trail for pricing changes"""

    __tablename__ = "pricing_history"

    id = Column(Integer, primary_key=True, index=True)
    template_id = Column(Integer, ForeignKey("pricing_templates.id", ondelete="SET NULL"))
    action = Column(String(50), nullable=False)  # 'activated', 'deactivated', 'created', 'updated'
    previous_template_id = Column(Integer)
    changed_by = Column(String, ForeignKey("users.id", ondelete="SET NULL"))
    changed_at = Column(TIMESTAMP, server_default=func.now(), index=True)
    notes = Column(Text)
    history_metadata = Column(JSONB)

    # Relationships
    template = relationship("PricingTemplate", back_populates="history")
    user = relationship("User", foreign_keys=[changed_by])

def __repr__(self):

        return f"<PricingHistory(action='{self.action}', template_id={self.template_id})>"


class UserPricingAssignment(Base):

    """User-specific pricing template assignment (for A/B testing)"""

    __tablename__ = "user_pricing_assignments"

    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    template_id = Column(Integer, ForeignKey("pricing_templates.id", ondelete="CASCADE"), nullable=False)
    assigned_at = Column(TIMESTAMP, server_default=func.now())
    assigned_by = Column(String(50), default="auto")  # 'admin', 'ab_test', 'region'

    # Relationships
    user = relationship("User")
    template = relationship("PricingTemplate")

def __repr__(self):

        return f"<UserPricingAssignment(user_id={self.user_id}, template_id={self.template_id})>"