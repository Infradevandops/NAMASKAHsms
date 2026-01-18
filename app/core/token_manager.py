"""Token management with refresh tokens and HttpOnly cookies - Task 1.2."""

from datetime import datetime, timedelta, timezone
from typing import Dict, Any, Optional
import secrets
from app.utils.security import create_access_token, verify_token


def create_tokens(user_id: str, email: str) -> Dict[str, str]:
    """Create access and refresh tokens - Task 1.2 Fix."""
    # Access token (24 hours)
    access_data = {"user_id": user_id, "email": email, "type": "access"}
    access_token = create_access_token(access_data, timedelta(hours=24))

    # Refresh token (30 days) - stored as secure random string
    refresh_token = secrets.token_urlsafe(32)

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "expires_in": 86400,  # 24 hours in seconds
    }


def verify_refresh_token(refresh_token: str) -> bool:
    """Verify refresh token format (basic check)."""
    return len(refresh_token) > 20 and isinstance(refresh_token, str)


def decode_access_token(token: str) -> Optional[Dict[str, Any]]:
    """Decode and verify access token."""
    payload = verify_token(token)
    if payload and payload.get("type") == "access":
        return payload
    return None


def get_refresh_token_expiry() -> datetime:
    """Get refresh token expiry datetime (30 days from now)."""
    return datetime.now(timezone.utc) + timedelta(days=30)
