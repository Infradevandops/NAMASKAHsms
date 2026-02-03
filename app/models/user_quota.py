"""Monthly quota usage tracking model."""

from sqlalchemy import Column, Float, ForeignKey, String, UniqueConstraint

from app.models.base import BaseModel


class UserQuota(BaseModel):
    """User quota model - alias for backwards compatibility."""

    __tablename__ = "user_quotas"

    user_id = Column(String(50), ForeignKey("users.id"), nullable=False, index=True)
    quota_limit = Column(Float, default=100.0, nullable=False)
    quota_used = Column(Float, default=0.0, nullable=False)


class MonthlyQuotaUsage(BaseModel):
    """Track monthly quota usage per user."""

    __tablename__ = "monthly_quota_usage"

    user_id = Column(String(50), ForeignKey("users.id"), nullable=False, index=True)
    month = Column(String(7), nullable=False, index=True)  # "2025-01"
    quota_used = Column(Float, default=0.0, nullable=False)
    overage_used = Column(Float, default=0.0, nullable=False)

    __table_args__ = (UniqueConstraint("user_id", "month", name="uq_user_month"),)
