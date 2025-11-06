"""Security utilities for password hashing, JWT tokens, and API keys."""

import secrets
import string
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional

import jwt
from passlib.context import CryptContext

from app.core.config import settings

# Password hashing context - using only pbkdf2_sha256
pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")


def hash_password(password: str) -> str:
    """Hash a password using pbkdf2_sha256."""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash."""
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(
    data: Dict[str, Any], expires_delta: Optional[timedelta] = None
) -> str:
    """Create a JWT access token."""
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(hours=settings.jwt_expiry_hours)

    to_encode.update({"exp": expire})

    return jwt.encode(to_encode, settings.secret_key, algorithm=settings.jwt_algorithm)


def verify_token(token: str) -> Optional[Dict[str, Any]]:
    """Verify and decode a JWT token."""
    try:
        payload = jwt.decode(
            token, settings.secret_key, algorithms=[settings.jwt_algorithm]
        )
        return payload
    except jwt.InvalidTokenError:
        return None


def generate_api_key(length: int = 32) -> str:
    """Generate a secure random API key."""
    alphabet = string.ascii_letters + string.digits
    return "".join(secrets.choice(alphabet) for _ in range(length))


def generate_verification_code(length: int = 6) -> str:
    """Generate a numeric verification code."""
    return "".join(secrets.choice(string.digits) for _ in range(length))


def generate_secure_id(prefix: str = "", length: int = 16) -> str:
    """Generate a secure random ID with optional prefix."""
    alphabet = string.ascii_lowercase + string.digits
    random_part = "".join(secrets.choice(alphabet) for _ in range(length))

    if prefix:
        return f"{prefix}_{random_part}"
    return random_part


def mask_sensitive_data(data: str, visible_chars: int = 4) -> str:
    """Mask sensitive data showing only first/last characters."""
    if len(data) <= visible_chars * 2:
        return "*" * len(data)

    return (
        data[:visible_chars]
        + "*" * (len(data) - visible_chars * 2)
        + data[-visible_chars:]
    )


def validate_password_strength(password: str) -> Dict[str, Any]:
    """Validate password strength and return requirements."""
    requirements = {
        "min_length": len(password) >= 8,
        "has_uppercase": any(c.isupper() for c in password),
        "has_lowercase": any(c.islower() for c in password),
        "has_digit": any(c.isdigit() for c in password),
        "has_special": any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in password),
    }

    is_valid = all(requirements.values())

    return {
        "is_valid": is_valid,
        "requirements": requirements,
        "score": sum(requirements.values()),
    }
