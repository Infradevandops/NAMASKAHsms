"""Whitelabel models for custom domain and branding"""

from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.models.base import Base


class WhitelabelDomain(Base):
    """Custom domain configuration for whitelabel"""

    __tablename__ = "whitelabel_custom_domains"
    __table_args__ = {"extend_existing": True}

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(
        String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    domain = Column(String(255), nullable=False, unique=True, index=True)
    verified = Column(Boolean, default=False, nullable=False)
    verification_token = Column(String(255), nullable=True)
    verification_method = Column(
        String(50), nullable=True
    )  # txt_record, meta_tag, file_upload
    ssl_status = Column(
        String(50), default="pending", nullable=False
    )  # pending, active, failed
    ssl_expires_at = Column(DateTime, nullable=True)
    active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(
        DateTime, default=func.now(), onupdate=func.now(), nullable=False
    )

    # Relationships
    user = relationship("User", back_populates="whitelabel_domains")

    def __repr__(self):
        return f"<WhitelabelDomain(domain={self.domain}, verified={self.verified})>"


class WhitelabelBranding(Base):
    """Custom branding configuration for whitelabel"""

    __tablename__ = "whitelabel_custom_branding"
    __table_args__ = {"extend_existing": True}

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(
        String,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )
    logo_url = Column(String(500), nullable=True)
    favicon_url = Column(String(500), nullable=True)
    primary_color = Column(String(7), default="#667eea", nullable=False)
    secondary_color = Column(String(7), default="#764ba2", nullable=False)
    accent_color = Column(String(7), default="#f093fb", nullable=False)
    font_family = Column(String(100), default="Inter", nullable=False)
    company_name = Column(String(255), nullable=True)
    support_email = Column(String(255), nullable=True)
    support_url = Column(String(500), nullable=True)
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(
        DateTime, default=func.now(), onupdate=func.now(), nullable=False
    )

    # Relationships
    user = relationship("User", back_populates="whitelabel_branding")

    def to_dict(self):
        """Convert to dictionary"""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "logo_url": self.logo_url,
            "favicon_url": self.favicon_url,
            "primary_color": self.primary_color,
            "secondary_color": self.secondary_color,
            "accent_color": self.accent_color,
            "font_family": self.font_family,
            "company_name": self.company_name,
            "support_email": self.support_email,
            "support_url": self.support_url,
        }

    def __repr__(self):
        return (
            f"<WhitelabelBranding(user_id={self.user_id}, company={self.company_name})>"
        )


class WhitelabelEmailTemplate(Base):
    """Custom email templates for whitelabel"""

    __tablename__ = "whitelabel_custom_email_templates"
    __table_args__ = {"extend_existing": True}

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(
        String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    template_name = Column(
        String(100), nullable=False
    )  # welcome, verification, payment, etc.
    subject = Column(String(255), nullable=True)
    html_content = Column(Text, nullable=True)
    text_content = Column(Text, nullable=True)
    active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(
        DateTime, default=func.now(), onupdate=func.now(), nullable=False
    )

    # Relationships
    user = relationship("User", back_populates="whitelabel_email_templates")

    def __repr__(self):
        return f"<WhitelabelEmailTemplate(user_id={self.user_id}, template={self.template_name})>"
