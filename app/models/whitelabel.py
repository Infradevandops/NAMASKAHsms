"""White-label configuration model."""

from datetime import datetime

from sqlalchemy import JSON, Boolean, Column, DateTime, String
from sqlalchemy.orm import relationship

from .base import Base


class WhiteLabelConfig(Base):
    """White-label configuration for partners."""

    __tablename__ = "whitelabel_config"

    id = Column(String(36), primary_key=True)
    partner_id = Column(String(36), nullable=False, unique=True)
    domain = Column(String(255), nullable=False)
    logo_url = Column(String(500))
    primary_color = Column(String(7))
    secondary_color = Column(String(7))
    company_name = Column(String(255))
    custom_css = Column(String)
    api_subdomain = Column(String(255))
    features = Column(JSON)
    custom_branding = Column(JSON)
    enabled = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    domains = relationship("WhiteLabelDomain", back_populates="config")
    themes = relationship("WhiteLabelTheme", back_populates="config")
    assets = relationship("WhiteLabelAsset", back_populates="config")

    def __repr__(self):

        return f"<WhiteLabelConfig(partner_id={self.partner_id}, domain={self.domain})>"