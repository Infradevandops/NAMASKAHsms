"""User quota model."""
from sqlalchemy import Column, Float, Integer, String, UniqueConstraint
from app.models.base import BaseModel

class UserQuota(BaseModel):
    """User monthly quota usage."""
    __tablename__ = "user_quotas"

    id = Column(String, primary_key=True)
    user_id = Column(String, nullable=False, index=True)
    month_year = Column(String, nullable=False) # YYYY-MM
    quota_used_usd = Column(Float, default=0.0)
    sms_count = Column(Integer, default=0)

    __table_args__ = (
        UniqueConstraint('user_id', 'month_year', name='uq_user_month'),
    )
