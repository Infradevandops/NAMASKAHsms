"""Authentication security: rate limiting, lockout, audit logging."""

import json
import uuid
from datetime import datetime, timedelta

from sqlalchemy import Boolean, Column, DateTime, String
from sqlalchemy.orm import Session

from app.core.logging import get_logger
from app.models.base import Base

logger = get_logger("auth_security")


class LoginAttempt(Base):
    """Track login attempts for rate limiting."""

    __tablename__ = "login_attempts"

    id = Column(String, primary_key=True)
    email = Column(String, index=True)
    ip_address = Column(String)
    success = Column(Boolean, default=False)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)


class AuthAuditLog(Base):
    """Audit log for authentication events."""

    __tablename__ = "auth_audit_logs"

    id = Column(String, primary_key=True)
    user_id = Column(String, index=True)
    event_type = Column(String)
    ip_address = Column(String)
    user_agent = Column(String)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    details = Column(String)


class AccountLockout(Base):
    """Track account lockouts."""

    __tablename__ = "account_lockouts"

    id = Column(String, primary_key=True)
    email = Column(String, unique=True, index=True)
    locked_until = Column(DateTime)
    reason = Column(String)
    timestamp = Column(DateTime, default=datetime.utcnow)


def check_rate_limit(
    db: Session,
    email: str,
    ip_address: str,
    max_attempts: int = 5,
    window_minutes: int = 15,
) -> bool:
    """Check if email/IP has exceeded rate limit."""
    try:
        cutoff = datetime.utcnow() - timedelta(minutes=window_minutes)
        failed_attempts = (
            db.query(LoginAttempt)
            .filter(
                LoginAttempt.email == email,
                LoginAttempt.ip_address == ip_address,
                LoginAttempt.success == False,
                LoginAttempt.timestamp > cutoff,
            )
            .count()
        )
        return failed_attempts < max_attempts
    except Exception as e:
        logger.error(f"Rate limit check error: {e}")
        return True


def check_account_lockout(db: Session, email: str) -> bool:
    """Check if account is locked."""
    try:
        lockout = (
            db.query(AccountLockout)
            .filter(
                AccountLockout.email == email,
                AccountLockout.locked_until > datetime.utcnow(),
            )
            .first()
        )
        return lockout is not None
    except Exception as e:
        logger.error(f"Account lockout check error: {e}")
        return False


def lock_account(
    db: Session,
    email: str,
    reason: str = "Too many failed login attempts",
    duration_minutes: int = 30,
):
    """Lock account temporarily."""
    try:
        lockout = AccountLockout(
            id=str(uuid.uuid4()),
            email=email,
            locked_until=datetime.utcnow() + timedelta(minutes=duration_minutes),
            reason=reason,
        )
        db.add(lockout)
        db.commit()
        logger.warning(f"Account locked: {email} - {reason}")
    except Exception as e:
        logger.error(f"Account lock error: {e}")
        db.rollback()


def record_login_attempt(db: Session, email: str, ip_address: str, success: bool):
    """Record login attempt."""
    try:
        attempt = LoginAttempt(
            id=str(uuid.uuid4()),
            email=email,
            ip_address=ip_address,
            success=success,
            timestamp=datetime.utcnow(),
        )
        db.add(attempt)
        db.commit()

        if not success:
            failed_count = (
                db.query(LoginAttempt)
                .filter(
                    LoginAttempt.email == email,
                    LoginAttempt.success == False,
                    LoginAttempt.timestamp > datetime.utcnow() - timedelta(minutes=15),
                )
                .count()
            )

            if failed_count >= 5:
                lock_account(db, email)
    except Exception as e:
        logger.error(f"Login attempt record error: {e}")
        db.rollback()


def audit_log_auth_event(
    db: Session,
    event_type: str,
    user_id: str = None,
    email: str = None,
    ip_address: str = None,
    user_agent: str = None,
    details: dict = None,
):
    """Log authentication event."""
    try:
        log = AuthAuditLog(
            id=str(uuid.uuid4()),
            user_id=user_id,
            event_type=event_type,
            ip_address=ip_address,
            user_agent=user_agent,
            details=json.dumps(details or {}),
            timestamp=datetime.utcnow(),
        )
        db.add(log)
        db.commit()
        logger.info(f"Auth event: {event_type} - {email or user_id}")
    except Exception as e:
        logger.error(f"Audit log error: {e}")
        db.rollback()
