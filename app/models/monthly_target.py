"""Monthly Growth Target model for institutional break-even tracking."""

from sqlalchemy import Boolean, Column, Integer, Numeric, String

from app.models.base import BaseModel


class MonthlyTarget(BaseModel):
    """Monthly signup and revenue goals."""

    __tablename__ = "monthly_targets"

    month = Column(String(7), nullable=False, unique=True, index=True)  # YYYY-MM
    target_count = Column(Integer, nullable=False, default=350)
    revenue_target = Column(Numeric(10, 2), nullable=False, default=4000.00)
    is_active = Column(Boolean, default=True, nullable=False)
    notes = Column(String(500), nullable=True)
