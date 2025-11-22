"""API Key model for programmatic access."""
from sqlalchemy import Column, String, DateTime, Boolean, ForeignKey, Integer
from datetime import datetime
from app.models.base import Base


class APIKey(Base):
    __tablename__ = "api_keys"

    id = Column(String(36), primary_key=True, default=lambda: str(__import__("uuid").uuid4()))
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    name = Column(String(100), nullable=False)
    key = Column(String(255), nullable=False, unique=True)
    is_active = Column(Boolean, default=True)
    request_count = Column(Integer, default=0)
    last_used = Column(DateTime, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
