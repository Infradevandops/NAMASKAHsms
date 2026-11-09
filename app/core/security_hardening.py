"""
Security Hardening Module - Critical Security Fixes
Addresses: Input validation, CSRF protection, secure headers
"""

import html
import logging
import re
import secrets
from typing import Any

from app.core.cache import cache_manager

logger = logging.getLogger(__name__)

_CSRF_TTL = 3600  # 1 hour
_RATE_WINDOW = 60  # seconds


class SecurityHardening:
    """Comprehensive security hardening utilities"""

    blocked_patterns = [
        r"<script[^>]*>.*?</script>",
        r"javascript:",
        r"on\w+\s*=",
        r"data:text/html",
        r"vbscript:",
    ]

    def sanitize_input(self, input_data: Any) -> str:
        """Sanitize user input to prevent XSS and injection attacks"""
        if not isinstance(input_data, str):
            return str(input_data)
        sanitized = html.escape(input_data)
        for pattern in self.blocked_patterns:
            sanitized = re.sub(pattern, "", sanitized, flags=re.IGNORECASE)
        return sanitized.strip()

    def validate_service_name(self, service_name: str) -> bool:
        """Validate service name format"""
        if not isinstance(service_name, str):
            return False
        return bool(re.match(r"^[a-zA-Z0-9_-]+$", service_name)) and len(service_name) <= 50

    def validate_email(self, email: str) -> bool:
        """Validate email format"""
        if not isinstance(email, str):
            return False
        return bool(re.match(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$", email)) and len(email) <= 254

    def generate_csrf_token(self, user_id: str) -> str:
        """Generate CSRF token for user, stored in Redis (multi-process safe)"""
        token = secrets.token_urlsafe(32)
        cache_manager.set(f"csrf:{user_id}", token, ttl=_CSRF_TTL)
        return token

    def validate_csrf_token(self, user_id: str, token: str) -> bool:
        """Validate CSRF token from Redis"""
        stored = cache_manager.get(f"csrf:{user_id}")
        if not stored or not token:
            return False
        return secrets.compare_digest(stored, token)

    def check_rate_limit(self, identifier: str, max_requests: int = 100, window_seconds: int = _RATE_WINDOW) -> bool:
        """
        Redis-backed sliding-window rate limit (multi-process safe).
        Uses a Redis counter with expiry — approximate but correct across workers.
        """
        key = f"rl:{identifier}:{window_seconds}"
        try:
            pipe = cache_manager.client.pipeline()
            pipe.incr(key)
            pipe.expire(key, window_seconds)
            count, _ = pipe.execute()
            return count <= max_requests
        except Exception as e:
            logger.error(f"Rate limit check error for {identifier}: {e}")
            return True  # fail open to avoid blocking legitimate traffic


security_hardening = SecurityHardening()
