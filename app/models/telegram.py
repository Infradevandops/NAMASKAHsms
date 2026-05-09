"""Telegram integration models"""

from sqlalchemy import (
    ARRAY,
    BigInteger,
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.models.base import Base


class TelegramConnection(Base):
    """User's Telegram connection"""

    __tablename__ = "telegram_connections"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True
    )
    chat_id = Column(BigInteger, nullable=False, unique=True, index=True)
    username = Column(String(255), nullable=True)
    first_name = Column(String(255), nullable=True)
    active = Column(Boolean, default=True, nullable=False, index=True)
    connected_at = Column(DateTime, default=func.now(), nullable=False)
    last_message_at = Column(DateTime, nullable=True)

    # Relationships
    user = relationship("User", back_populates="telegram_connection")

    def __repr__(self):
        return f"<TelegramConnection(user_id={self.user_id}, chat_id={self.chat_id}, active={self.active})>"


class TelegramForwardingRule(Base):
    """User's Telegram forwarding preferences"""

    __tablename__ = "telegram_forwarding_rules"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True
    )
    forward_all = Column(Boolean, default=True, nullable=False)
    service_filter = Column(ARRAY(String), nullable=True)  # Only forward these services
    country_filter = Column(
        ARRAY(String), nullable=True
    )  # Only forward these countries
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(
        DateTime, default=func.now(), onupdate=func.now(), nullable=False
    )

    # Relationships
    user = relationship("User", back_populates="telegram_forwarding_rule")

    def __repr__(self):
        return f"<TelegramForwardingRule(user_id={self.user_id}, forward_all={self.forward_all})>"
