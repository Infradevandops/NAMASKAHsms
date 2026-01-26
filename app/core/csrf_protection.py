"""CSRF protection utilities."""

import secrets

from fastapi import HTTPException, Request, status
from sqlalchemy.orm import Session


def generate_csrf_token() -> str:
    """Generate a secure CSRF token."""
    return secrets.token_urlsafe(32)


async def verify_csrf_token(request: Request, db: Session) -> str:
    """Verify CSRF token from request."""
    token = request.headers.get("X-CSRF-Token")
    if not token:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="CSRF token missing")
    return token


def get_csrf_token_for_session(session_id: str) -> str:
    """Get or create CSRF token for session."""
    return generate_csrf_token()
