"""Carrier analytics model for tracking carrier preferences vs actual assignments."""

from datetime import datetime, timezone
from sqlalchemy import Boolean, Column, DateTime, Float, String, Integer

from app.models.base import BaseModel


class CarrierAnalytics(BaseModel):
    """Track carrier preference requests and outcomes.
    
    This model records every carrier preference request to enable:
    - Analytics on carrier preference success rates
    - Reporting on which carriers are most requested vs assigned
    - Identifying TextVerified carrier availability patterns
    - Optimizing carrier recommendations
    """

    __tablename__ = "carrier_analytics"

    # Reference fields
    verification_id = Column(String, nullable=False, index=True)
    user_id = Column(String, nullable=False, index=True)

    # Carrier preference tracking
    requested_carrier = Column(String, nullable=False)  # What user asked for (e.g., "verizon")
    sent_to_textverified = Column(String, nullable=False)  # Normalized value sent to API
    textverified_response = Column(String)  # What TextVerified returned (e.g., "Mobile")
    
    # Assignment details
    assigned_phone = Column(String)  # Phone number assigned
    assigned_area_code = Column(String)  # Area code of assigned number
    
    # Outcome tracking
    outcome = Column(String)  # accepted, cancelled, timeout, completed, error
    exact_match = Column(Boolean, default=False)  # Did assigned match requested?
    
    # Timestamps
    created_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc), index=True)
