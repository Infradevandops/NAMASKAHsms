"""Enhanced white - label models."""

from sqlalchemy import JSON, Boolean, Column, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from app.models.base import BaseModel


class WhiteLabelDomain(BaseModel):

    __tablename__ = "whitelabel_domains"

    config_id = Column(String, ForeignKey("whitelabel_config.id"), nullable=False)
    domain = Column(String(255), nullable=False, unique=True, index=True)
    subdomain = Column(String(100), nullable=True)
    ssl_enabled = Column(Boolean, default=False)
    ssl_cert_path = Column(String(500), nullable=True)
    dns_verified = Column(Boolean, default=False)
    is_primary = Column(Boolean, default=False)

    # Relationships
    config = relationship("WhiteLabelConfig", back_populates="domains")


class WhiteLabelTheme(BaseModel):

    __tablename__ = "whitelabel_themes"

    config_id = Column(String, ForeignKey("whitelabel_config.id"), nullable=False)
    name = Column(String(100), nullable=False)
    css_variables = Column(JSON, default=lambda: {})
    custom_css = Column(Text, nullable=True)
    font_family = Column(String(100), default="Inter, sans - serif")
    logo_variants = Column(JSON, default=lambda: {})
    is_active = Column(Boolean, default=True)

    # Relationships
    config = relationship("WhiteLabelConfig", back_populates="themes")


class WhiteLabelAsset(BaseModel):

    __tablename__ = "whitelabel_assets"

    config_id = Column(String, ForeignKey("whitelabel_config.id"), nullable=False)
    asset_type = Column(String(50), nullable=False)  # logo, favicon, background
    file_path = Column(String(500), nullable=False)
    file_name = Column(String(255), nullable=False)
    file_size = Column(Integer, nullable=True)
    mime_type = Column(String(100), nullable=True)
    cdn_url = Column(String(500), nullable=True)
    is_active = Column(Boolean, default=True)

    # Relationships
    config = relationship("WhiteLabelConfig", back_populates="assets")


class PartnerFeature(BaseModel):

    __tablename__ = "partner_features"

    partner_id = Column(String, ForeignKey("users.id"), nullable=False)
    feature_key = Column(String(100), nullable=False)
    is_enabled = Column(Boolean, default=True)
    configuration = Column(JSON, default=lambda: {})
    usage_limit = Column(Integer, nullable=True)
    usage_count = Column(Integer, default=0)

    # Relationships
    partner = relationship("User", back_populates="partner_features")