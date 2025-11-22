"""Token management with refresh tokens and HttpOnly cookies."""
from datetime import timedelta
from typing import Dict, Any, Optional
import secrets
from app.utils.security import create_access_token, verify_token


def create_tokens(user_id: str, email: str) -> Dict[str, str]:
    """Create access and refresh tokens."""
    # Short-lived access token (15 minutes)
    access_data = {"user_id": user_id, "email": email}
    access_token = create_access_token(access_data, timedelta(minutes=15))

    # Long-lived refresh token (30 days)
    refresh_token = secrets.token_urlsafe(32)

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "expires_in": 900  # 15 minutes in seconds
    }


def verify_refresh_token(refresh_token: str) -> bool:
    """Verify refresh token format (basic check)."""
    return len(refresh_token) > 20


def decode_access_token(token: str) -> Optional[Dict[str, Any]]:
    """Decode and verify access token."""
    return verify_token(token)
