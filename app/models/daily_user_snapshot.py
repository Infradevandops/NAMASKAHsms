"""Daily User Snapshot model for historical growth forensics."""

from sqlalchemy import Column, Date, Integer, Numeric

from app.models.base import BaseModel


class DailyUserSnapshot(BaseModel):
    """Point-in-time snapshot of platform growth metrics."""

    __tablename__ = "daily_user_snapshots"

    snapshot_date = Column(Date, nullable=False, unique=True, index=True)
    total_users = Column(Integer, nullable=False)
    new_users = Column(Integer, nullable=False, default=0)
    active_users_24h = Column(Integer, nullable=False, default=0)
    daily_revenue = Column(Numeric(10, 2), nullable=False, default=0.00)
    
    # Tier breakdown
    freemium_count = Column(Integer, default=0)
    payg_count = Column(Integer, default=0)
    pro_count = Column(Integer, default=0)
    custom_count = Column(Integer, default=0)
