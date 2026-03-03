"""Security configuration and utilities."""


import re
import secrets
from typing import Any

from app.core.config import get_settings


class SecurityConfig:
    """Security configuration management."""

    SENSITIVE_PATTERNS = [
        "password", "token", "secret", "key", "api_key", "auth_token",
        "bearer", "authorization", "credit_card", "ssn", "social_security",
        "private_key", "certificate", "credentials", "session_id",
    ]

    SENSITIVE_HEADERS = [
        "authorization", "x-api-key", "cookie", "x-auth-token",
        "bearer", "x-session-id", "x-csrf-token",
    ]

    SENSITIVE_PARAMS = [
        "password", "token", "key", "secret", "api_key", "auth", "session", "signature",
    ]

    ALLOWED_HOSTS = [
        "namaskah.onrender.com",
        "api.namaskah.com",
        "localhost",
        "127.0.0.1",
    ]

    SECURITY_HEADERS = {
        "X-Content-Type-Options": "nosniff",
        "X-Frame-Options": "DENY",
        "X-XSS-Protection": "1; mode=block",
        "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
        "Referrer-Policy": "strict-origin-when-cross-origin",
    }

    @staticmethod
    def is_sensitive_key(key: str) -> bool:
        """Check if a key contains sensitive information."""
        key_lower = key.lower()
        return any(pattern in key_lower for pattern in SecurityConfig.SENSITIVE_PATTERNS)

    @staticmethod
    def sanitize_data(data: Any) -> Any:
        """Recursively sanitize sensitive data."""
        if isinstance(data, dict):
            sanitized = {}
            for key, value in data.items():
                if SecurityConfig.is_sensitive_key(key):
                    sanitized[key] = "[REDACTED]"
                elif isinstance(value, (dict, list)):
                    sanitized[key] = SecurityConfig.sanitize_data(value)
                else:
                    sanitized[key] = value
            return sanitized
        elif isinstance(data, list):
            return [SecurityConfig.sanitize_data(item) for item in data]
        else:
            return data

    @staticmethod
    def validate_host(host: str) -> bool:
        """Validate if host is allowed."""
        settings = get_settings()
        if settings.environment == "development":
            return True
        return host in SecurityConfig.ALLOWED_HOSTS

    @staticmethod
    def generate_secure_token(length: int = 32) -> str:
        """Generate cryptographically secure token."""
        return secrets.token_urlsafe(length)

    @staticmethod
    def sanitize_headers(headers: dict) -> dict:
        """Sanitize sensitive headers for logging."""
        sanitized = {}
        for key, value in headers.items():
            if key.lower() in SecurityConfig.SENSITIVE_HEADERS:
                sanitized[key] = "[REDACTED]"
            else:
                sanitized[key] = value
        return sanitized
