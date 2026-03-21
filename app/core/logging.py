"""Logging configuration for Namaskah application."""

import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional


def setup_logging():
    """Setup logging configuration."""
    handlers = [logging.StreamHandler(sys.stdout)]

    # Only create file handler in development (not on Render/production)
    if os.environ.get("RENDER") is None:
        try:
            log_dir = Path("logs")
            log_dir.mkdir(exist_ok=True)
            handlers.append(logging.FileHandler(log_dir / "app.log"))
        except (PermissionError, OSError):
            # Can't create logs directory, use stdout only
            pass

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=handlers,
    )


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance."""
    return logging.getLogger(name)


def log_tier_access(
    user_id: str, tier: str, feature: str, allowed: bool, reason: str = ""
) -> None:
    """Log all tier-based access decisions.

    This function logs every time a user attempts to access a feature,
    whether they were allowed or denied, and why. This creates an audit
    trail for compliance and debugging.

    Args:
        user_id: User ID attempting access
        tier: User's current tier
        feature: Feature being accessed
        allowed: Whether access was allowed
        reason: Reason for allow/deny decision
    """
    logger = get_logger("tier_access")
    status = "ALLOWED" if allowed else "DENIED"
    timestamp = datetime.now().isoformat()

    log_message = (
        f"TIER_ACCESS | timestamp={timestamp} | status={status} | "
        f"user={user_id} | tier={tier} | feature={feature}"
    )

    if reason:
        log_message += f" | reason={reason}"

    if allowed:
        logger.info(log_message)
    else:
        logger.warning(log_message)


def log_tier_change(
    user_id: str, old_tier: str, new_tier: str, reason: str = ""
) -> None:
    """Log tier changes.

    This function logs every time a user's tier is changed, including
    upgrades, downgrades, and automatic expirations. This creates an
    audit trail for billing and compliance.

    Args:
        user_id: User ID whose tier changed
        old_tier: Previous tier
        new_tier: New tier
        reason: Reason for tier change (e.g., 'upgrade', 'expiration', 'downgrade')
    """
    logger = get_logger("tier_change")
    timestamp = datetime.now().isoformat()

    log_message = (
        f"TIER_CHANGE | timestamp={timestamp} | user={user_id} | "
        f"old_tier={old_tier} | new_tier={new_tier}"
    )

    if reason:
        log_message += f" | reason={reason}"

    logger.info(log_message)


def log_unauthorized_access(
    user_id: str, tier: str, feature: str, required_tier: Optional[str] = None
) -> None:
    """Log unauthorized access attempts.

    This function logs when a user attempts to access a feature they
    don't have permission for. This helps identify potential security
    issues or user confusion.

    Args:
        user_id: User ID attempting unauthorized access
        tier: User's current tier
        feature: Feature being accessed
        required_tier: Minimum tier required for feature
    """
    logger = get_logger("security")
    timestamp = datetime.now().isoformat()

    log_message = (
        f"UNAUTHORIZED_ACCESS | timestamp={timestamp} | user={user_id} | "
        f"tier={tier} | feature={feature}"
    )

    if required_tier:
        log_message += f" | required_tier={required_tier}"

    logger.warning(log_message)
