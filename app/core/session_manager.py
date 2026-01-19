"""Session management for tracking active user sessions."""

import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy import Boolean, Column, DateTime, String

from app.models.base import Base


class UserSession(Base):
    """Track active user sessions."""

    __tablename__ = "user_sessions"

    id = Column(String, primary_key=True)
    user_id = Column(String, index=True)
    refresh_token = Column(String, unique=True)
    ip_address = Column(String)
    user_agent = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    expires_at = Column(DateTime, index=True)
    is_active = Column(Boolean, default=True)


def create_session(
    db,
    user_id: str,
    ip_address: str,
    user_agent: str,
    refresh_token: str,
    expires_days: int = 30,
):
    """Create new user session."""
    session = UserSession(
        id=str(uuid.uuid4()),
        user_id=user_id,
        refresh_token=refresh_token,
        ip_address=ip_address,
        user_agent=user_agent,
        expires_at=datetime.now(timezone.utc) + timedelta(days=expires_days),
    )
    db.add(session)
    db.commit()
    return session


def get_session(db, refresh_token: str):
    """Get active session by refresh token."""
    session = (
        db.query(UserSession)
        .filter(
            UserSession.refresh_token == refresh_token,
            UserSession.is_active,
            UserSession.expires_at > datetime.utcnow(),
        )
        .first()
    )
    return session


def invalidate_session(db, refresh_token: str):
    """Invalidate session."""
    session = (
        db.query(UserSession).filter(UserSession.refresh_token == refresh_token).first()
    )
    if session:
        session.is_active = False
        db.commit()


def invalidate_all_sessions(db, user_id: str):
    """Invalidate all sessions for user."""
    db.query(UserSession).filter(UserSession.user_id == user_id).update(
        {"is_active": False}
    )
    db.commit()
