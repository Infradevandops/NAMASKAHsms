"""API Key model for programmatic access."""

from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String

from app.models.base import Base


class APIKey(Base):

    __tablename__ = "api_keys"

    id = Column(String(36), primary_key=True, default=lambda: str(__import__("uuid").uuid4()))
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    name = Column(String(100), nullable=False)
    key_hash = Column(String(255), nullable=False, unique=True)  # Hashed key for security
    key_preview = Column(String(20), nullable=False)  # Last 4 chars for display
    is_active = Column(Boolean, default=True)
    request_count = Column(Integer, default=0)
    last_used = Column(DateTime, nullable=True)
    expires_at = Column(DateTime, nullable=True)  # Optional expiration
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)