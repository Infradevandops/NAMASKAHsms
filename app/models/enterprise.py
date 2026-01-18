"""Enterprise SLA and account management models."""

from sqlalchemy import Column, String, Integer, Float, Boolean, JSON, ForeignKey
from sqlalchemy.orm import relationship
from app.models.base import BaseModel


class EnterpriseTier(BaseModel):
    __tablename__ = "enterprise_tiers"

    name = Column(String(50), nullable=False, unique=True)
    min_monthly_spend = Column(Float, nullable=False)
    sla_uptime = Column(Float, default=99.9)  # percentage
    max_response_time = Column(Integer, default=2000)  # milliseconds
    priority_support = Column(Boolean, default=False)
    dedicated_manager = Column(Boolean, default=False)
    custom_rates = Column(JSON, default=lambda: {})
    features = Column(
        JSON,
        default=lambda: {"api_rate_limit": 1000, "webhook_retries": 3, "analytics_retention": 90},
    )


class EnterpriseAccount(BaseModel):
    __tablename__ = "enterprise_accounts"

    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    tier_id = Column(String, ForeignKey("enterprise_tiers.id"), nullable=False)
    account_manager_email = Column(String(255), nullable=True)
    monthly_spend = Column(Float, default=0.0)
    sla_credits = Column(Float, default=0.0)  # SLA violation credits

    # Relationships
    user = relationship("User", back_populates="enterprise_account")
    tier = relationship("EnterpriseTier")
