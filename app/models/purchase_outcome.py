from datetime import datetime

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    SmallInteger,
    String,
    func,
)
from sqlalchemy.orm import relationship

from app.core.database import Base


class PurchaseOutcome(Base):
    __tablename__ = "purchase_outcomes"

    id = Column(Integer, primary_key=True, index=True)
    service = Column(String(100), nullable=False, index=True)
    requested_code = Column(String(10), nullable=True)
    assigned_code = Column(String(10), nullable=False)
    assigned_carrier = Column(String(50), nullable=True)
    carrier_type = Column(String(20), nullable=True)
    assigned_city = Column(String(100), nullable=True)
    assigned_state = Column(String(2), nullable=True)
    matched = Column(Boolean, nullable=True)
    sms_received = Column(Boolean, nullable=True)

    user_id = Column(String, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    verification_id = Column(
        String, ForeignKey("verifications.id", ondelete="SET NULL"), nullable=True
    )

    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False, index=True
    )
    hour_utc = Column(SmallInteger, nullable=True)
    day_of_week = Column(SmallInteger, nullable=True)

    # Institutional Grade Telemetry
    provider = Column(String(50), nullable=True, index=True)
    country = Column(String(5), nullable=True, index=True)
    raw_sms_code = Column(String(50), nullable=True)
    latency_seconds = Column(Float, nullable=True)
 
    # Financial Telemetry
    is_refunded = Column(Boolean, default=False, index=True)
    refund_amount = Column(Float, default=0.0)
    refund_reason = Column(String(100), nullable=True)  # "sms_timeout", "area_code_mismatch", etc.
    provider_cost = Column(Float, nullable=True)     # Total credits paid to the provider
    user_price = Column(Float, nullable=True)        # Total credits paid by the user

    # Phase 6.4 Alternative Tracking
    selected_from_alternatives = Column(Boolean, nullable=True, default=False)
    original_request = Column(String(10), nullable=True)

    # Relationships (optional but useful if needed)
    # user = relationship("User", back_populates="purchase_outcomes")
    # verification = relationship("Verification", back_populates="purchase_outcome")

    __table_args__ = (
        Index("ix_po_svc_assigned_date", "service", "assigned_code", "created_at"),
        Index("ix_po_svc_requested_date", "service", "requested_code", "created_at"),
        Index("ix_po_carrier_svc", "assigned_carrier", "service"),
    )
