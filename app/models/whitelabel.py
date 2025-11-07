"""White-label configuration model."""
from sqlalchemy import Column, String, Boolean, Text, JSON
from app.models.base import BaseModel

class WhiteLabelConfig(BaseModel):
    __tablename__ = "whitelabel_configs"
    
    domain = Column(String(255), nullable=False, unique=True, index=True)
    company_name = Column(String(100), nullable=False)
    logo_url = Column(String(500), nullable=True)
    primary_color = Column(String(7), default="#667eea")
    secondary_color = Column(String(7), default="#10b981")
    custom_css = Column(Text, nullable=True)
    api_subdomain = Column(String(100), nullable=True)
    is_active = Column(Boolean, default=True)
    features = Column(JSON, default=lambda: {
        "sms": True,
        "whatsapp": True,
        "telegram": True,
        "analytics": True
    })