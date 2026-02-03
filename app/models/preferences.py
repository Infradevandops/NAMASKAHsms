"""User preferences model."""

from sqlalchemy import JSON, Column, String
from app.models.base import BaseModel


class ServicePreference(BaseModel):
    """User preferences for services."""

    __tablename__ = "service_preferences"

    user_id = Column(String, nullable=False, index=True)
    service_name = Column(String, nullable=False, index=True)

    # Preferred settings
    preferred_country = Column(String)
    preferred_operator = Column(String, default="any")
    preferred_tier = Column(String, default="standard")
    preferred_capability = Column(String, default="sms")

    # Additional preferences as JSON
    preferences_data = Column(JSON)

    # Usage tracking
    use_count = Column(String, default="0")
