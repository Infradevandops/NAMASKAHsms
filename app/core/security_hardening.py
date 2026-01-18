"""
Security Hardening Module - Critical Security Fixes
Addresses: Input validation, CSRF protection, secure headers
"""

import html
import logging
import re
import secrets
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

        # HTML escape
        sanitized = html.escape(input_data)

        # Remove dangerous patterns
        for pattern in self.blocked_patterns:
            sanitized = re.sub(pattern, "", sanitized, flags=re.IGNORECASE)

        return sanitized.strip()

    def validate_service_name(self, service_name: str) -> bool:
        """Validate service name format"""
        if not isinstance(service_name, str):
            return False

        # Allow only alphanumeric, hyphens, underscores
        pattern = r"^[a - zA-Z0 - 9_-]+$"
        return bool(re.match(pattern, service_name)) and len(service_name) <= 50

    def validate_email(self, email: str) -> bool:
        """Validate email format"""
        if not isinstance(email, str):
            return False

        pattern = r"^[a - zA-Z0 - 9._%+-]+@[a - zA-Z0 - 9.-]+\.[a - zA-Z]{2,}$"
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

        # Constant - time comparison
        return secrets.compare_digest(stored_token, token)

    def check_rate_limit(
        self, identifier: str, max_requests: int = 10, window_seconds: int = 60
    ) -> bool:
        """Check if request is within rate limit"""
        import time

        current_time = time.time()
        window_start = current_time - window_seconds

        if identifier not in self.rate_limits:
            self.rate_limits[identifier] = []

        # Remove old requests
        self.rate_limits[identifier] = [
            req_time for req_time in self.rate_limits[identifier] if req_time > window_start
        ]

        # Check limit
        if len(self.rate_limits[identifier]) >= max_requests:
            return False

        # Add current request
        self.rate_limits[identifier].append(current_time)
        return True

    def get_security_headers(self) -> Dict[str, str]:
        """Get security headers for responses"""
        return {
            "X - Content-Type - Options": "nosnif",
            "X - Frame-Options": "DENY",
            "X - XSS-Protection": "1; mode = block",
            "Strict - Transport-Security": "max - age = 31536000; includeSubDomains",
            "Content - Security-Policy": (
                "default - src 'self'; "
                "script - src 'self' 'unsafe - inline' https://cdnjs.cloudflare.com; "
                "style - src 'self' 'unsafe - inline' https://fonts.googleapis.com; "
                "font - src 'self' https://fonts.gstatic.com; "
                "img - src 'self' data: https:; "
                "connect - src 'self'; "
                "frame - ancestors 'none';"
            ),
            "Referrer - Policy": "strict - origin-when - cross-origin",
            "Permissions - Policy": "geolocation=(), microphone=(), camera=()",
        }

    def validate_request_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate and sanitize request data"""
        if not isinstance(data, dict):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid request data format",
            )

        sanitized_data = {}

        for key, value in data.items():
            # Sanitize key
            safe_key = self.sanitize_input(key)

            # Sanitize value based on type
            if isinstance(value, str):
                safe_value = self.sanitize_input(value)
            elif isinstance(value, (int, float, bool)):
                safe_value = value
            elif isinstance(value, list):
                safe_value = [self.sanitize_input(str(item)) for item in value]
            else:
                safe_value = self.sanitize_input(str(value))

            sanitized_data[safe_key] = safe_value

        return sanitized_data

    def log_security_event(
        self,
        event_type: str,
        details: Dict[str, Any],
        request: Optional[Request] = None,
    ):
        """Log security events for monitoring"""
        log_data = {
            "event_type": event_type,
            "timestamp": __import__("datetime").datetime.utcnow().isoformat(),
            "details": details,
        }

        if request:
            log_data.update(
                {
                    "client_ip": request.client.host if request.client else "unknown",
                    "user_agent": request.headers.get("user - agent", "unknown"),
                    "path": request.url.path,
                    "method": request.method,
                }
            )

        logger.warning("Security Event: %s", event_type, extra=log_data)


# Global security instance
security_hardening = SecurityHardening()


def secure_response(data: Any, headers: Optional[Dict[str, str]] = None) -> JSONResponse:
    """Create secure JSON response with security headers"""
    response_headers = security_hardening.get_security_headers()

    if headers:
        response_headers.update(headers)

    return JSONResponse(content=data, headers=response_headers)


def validate_and_sanitize_service_data(service_data: Dict[str, Any]) -> Dict[str, Any]:
    """Validate and sanitize service - related data"""
    required_fields = ["service"]

    # Check required fields
    for field in required_fields:
        if field not in service_data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Missing required field: {field}",
            )

    # Validate service name
    service_name = service_data.get("service", "")
    if not security_hardening.validate_service_name(service_name):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid service name format",
        )

    # Validate capability
    capability = service_data.get("capability", "sms")
    if capability not in ["sms", "voice"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid capability. Must be 'sms' or 'voice'",
        )

    # Validate country code
    country = service_data.get("country", "US")
    if not re.match(r"^[A - Z]{2}$", country):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid country code format",
        )

    return {
        "service": security_hardening.sanitize_input(service_name).lower(),
        "capability": capability,
        "country": country,
    }


# Middleware for automatic security hardening


class SecurityMiddleware:
    """Middleware to apply security hardening automatically"""

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] == "http":
            request = Request(scope, receive)

            # Rate limiting
            client_ip = request.client.host if request.client else "unknown"
            if not security_hardening.check_rate_limit(
                client_ip, max_requests=100, window_seconds=60
            ):
                response = JSONResponse(
                    content={"error": "Rate limit exceeded"},
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    headers=security_hardening.get_security_headers(),
                )
                await response(scope, receive, send)
                return

        await self.app(scope, receive, send)
