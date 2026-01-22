"""Verification Preset model."""

from sqlalchemy import Column, String, ForeignKey
from sqlalchemy.orm import relationship

from app.models.base import BaseModel

class VerificationPreset(BaseModel):
    """User saved verification filter presets."""
    
    __tablename__ = "verification_presets"

    user_id = Column(String, nullable=False, index=True)
    name = Column(String(50), nullable=False) # e.g. "My NY WhatsApp"
    
    # Filter configurations
    service_id = Column(String(50), nullable=False)
    country_id = Column(String(10), default="US")
    area_code = Column(String(10), nullable=True)
    carrier = Column(String(50), nullable=True)
    
    # Optional: preset_type (personal, system) if we want shared presets later
