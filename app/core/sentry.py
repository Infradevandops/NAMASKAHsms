"""Sentry configuration for error tracking and monitoring.

Integrates Sentry for:
- Error tracking and reporting
- Performance monitoring
- Release tracking
- User feedback
"""

import logging

import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.integrations.logging import LoggingIntegration
from sentry_sdk.integrations.redis import RedisIntegration
from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration
from sentry_sdk.integrations.threading import ThreadingIntegration

from app.core.config import get_settings

logger = logging.getLogger(__name__)


def init_sentry():
    """Initialize Sentry for error tracking and monitoring."""
    settings = get_settings()

    if not settings.sentry_dsn:
        logger.warning("Sentry DSN not configured, error tracking disabled")
        return

    sentry_sdk.init(
        dsn=settings.sentry_dsn,
        environment=settings.environment,
        release=settings.version,
        traces_sample_rate=settings.sentry_traces_sample_rate,
        profiles_sample_rate=settings.sentry_profiles_sample_rate,
        integrations=[
            FastApiIntegration(),
            SqlalchemyIntegration(),
            RedisIntegration(),
            LoggingIntegration(
                level=logging.INFO,
                event_level=logging.ERROR,
            ),
            ThreadingIntegration(),
        ],
        # Performance monitoring
        enable_tracing=True,
        # Capture breadcrumbs
        max_breadcrumbs=50,
        # Attach stack traces
        attach_stacktrace=True,
        # Include local variables in stack traces
        include_local_variables=True,
        # Ignore certain errors
        ignore_errors=[
            "KeyboardInterrupt",
            "SystemExit",
        ],
        # Before send hook for filtering
        before_send=before_send_sentry,
    )

    logger.info(f"Sentry initialized: {settings.environment} v{settings.version}")


def before_send_sentry(event, hint):
    """Filter events before sending to Sentry."""
    # Don't send 404 errors
    if event.get("request", {}).get("url", "").endswith("404"):
        return None

    # Don't send health check errors
    if "/health" in event.get("request", {}).get("url", ""):
        return None

    # Don't send auth errors for invalid credentials
    if (
        event.get("exception", {}).get("values", [{}])[0].get("type")
        == "InvalidCredentials"
    ):
        return None

    return event


def capture_tier_error(user_id: str, tier: str, error: Exception, context: dict = None):
    """Capture tier-related errors with context."""
    with sentry_sdk.push_scope() as scope:
        scope.set_user({"id": user_id})
        scope.set_context("tier", {"user_id": user_id, "tier": tier, **(context or {})})
        scope.set_tag("error_type", "tier_identification")
        sentry_sdk.capture_exception(error)


def capture_performance_metric(metric_name: str, value: float, tags: dict = None):
    """Capture performance metrics."""
    with sentry_sdk.push_scope() as scope:
        if tags:
            for key, val in tags.items():
                scope.set_tag(key, val)
        scope.set_context(
            "performance",
            {
                "metric": metric_name,
                "value": value,
            },
        )


def set_user_context(user_id: str, tier: str = None, email: str = None):
    """Set user context for Sentry."""
    sentry_sdk.set_user(
        {
            "id": user_id,
            "email": email,
        }
    )
    if tier:
        sentry_sdk.set_context("user_tier", {"tier": tier})


def clear_user_context():
    """Clear user context."""
    sentry_sdk.set_user(None)
