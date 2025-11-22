"""API Key model for programmatic access."""
from sqlalchemy import Boolean, Column, DateTime, String

from app.models.base import BaseModel


class APIKey(BaseModel):
    __tablename__ = "api_keys"

    user_id = Column(String(36), nullable=False, index=True)
    name = Column(String(100), nullable=False)
    key_hash = Column(String(255), nullable=False, unique=True)
    prefix = Column(String(10), nullable=False)
    is_active = Column(Boolean, default=True)
    last_used = Column(DateTime, nullable=True)
    expires_at = Column(DateTime, nullable=True)
