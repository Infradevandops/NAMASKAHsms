"""Cloudflare Turnstile verification."""

import os
from typing import Optional

import httpx

from app.core.logging import get_logger

logger = get_logger(__name__)

TURNSTILE_SECRET = os.getenv("TURNSTILE_SECRET_KEY", "")
TURNSTILE_VERIFY_URL = "https://challenges.cloudflare.com/turnstile/v0/siteverify"


async def verify_turnstile(token: Optional[str]) -> bool:
    """
    Verify a Cloudflare Turnstile token server-side.

    Returns True if valid or if Turnstile is not configured (dev mode).
    Returns False if token is missing or invalid in production.
    """
    if not TURNSTILE_SECRET:
        # Not configured — allow through (dev/test environment)
        logger.debug("Turnstile secret not set — skipping verification")
        return True

    if not token:
        logger.warning("Turnstile token missing")
        return False

    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.post(
                TURNSTILE_VERIFY_URL,
                data={"secret": TURNSTILE_SECRET, "response": token},
            )
            result = resp.json()
            success = result.get("success", False)
            if not success:
                logger.warning(
                    f"Turnstile verification failed: {result.get('error-codes', [])}"
                )
            return success
    except Exception as e:
        logger.error(f"Turnstile verification error: {e}")
        # Fail open on network error — don't block legitimate users
        return True
