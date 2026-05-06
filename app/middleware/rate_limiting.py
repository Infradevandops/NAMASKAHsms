"""
Rate Limiting Middleware (legacy stub).

Actual rate limiting is handled by app.core.unified_rate_limiting.
This module exists only for backward compatibility with imports.
"""

limiter = None


def get_limiter():
    return None
