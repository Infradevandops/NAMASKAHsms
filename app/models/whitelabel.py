"""White-label configuration model."""

from sqlalchemy import JSON, Boolean, Column, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from .base import BaseModel


class WhiteLabelConfig(BaseModel):
    """White-label configuration for partners."""

    __tablename__ = "whitelabel_config"

    partner_id = Column(UUID(as_uuid=False), nullable=False, unique=True)
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

    domains = relationship("WhiteLabelDomain", back_populates="config")
    themes = relationship("WhiteLabelTheme", back_populates="config")
    assets = relationship("WhiteLabelAsset", back_populates="config")

    def __repr__(self):

        return f"<WhiteLabelConfig(partner_id={self.partner_id}, domain={self.domain})>"