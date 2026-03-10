"""
Security Hardening Module - Critical Security Fixes
Addresses: Input validation, CSRF protection, secure headers
"""

import html
import logging
import re
import secrets
import time
from typing import Any, Dict, Optional

from fastapi import HTTPException, Request, status

logger = logging.getLogger(__name__)


class SecurityHardening:
    """Comprehensive security hardening utilities"""

    def __init__(self):
        self.csrf_tokens = {}
        self.rate_limits = {}
        self.blocked_patterns = [
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

        pattern = r"^[a-zA-Z0-9_-]+$"
        return bool(re.match(pattern, service_name)) and len(service_name) <= 50

    def validate_email(self, email: str) -> bool:
        """Validate email format"""
        if not isinstance(email, str):
            return False

        pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
        return bool(re.match(pattern, email)) and len(email) <= 254

    def generate_csrf_token(self, user_id: str) -> str:
        """Generate CSRF token for user"""
        token = secrets.token_urlsafe(32)
        self.csrf_tokens[user_id] = token
        return token

    def validate_csrf_token(self, user_id: str, token: str) -> bool:
        """Validate CSRF token"""
        stored_token = self.csrf_tokens.get(user_id)
        if not stored_token or not token:
            return False
        return secrets.compare_digest(stored_token, token)

    def check_rate_limit(
        self, identifier: str, max_requests: int = 100, window_seconds: int = 60
    ) -> bool:
        """Check if identifier has exceeded rate limit"""
        now = time.time()
        if identifier not in self.rate_limits:
            self.rate_limits[identifier] = []

        self.rate_limits[identifier] = [
            t for t in self.rate_limits[identifier] if now - t < window_seconds
        ]

        if len(self.rate_limits[identifier]) >= max_requests:
            return False

        self.rate_limits[identifier].append(now)
        return True


security_hardening = SecurityHardening()
