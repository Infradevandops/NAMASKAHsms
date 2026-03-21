"""Security middleware - comprehensive security headers."""

import base64
import os

from starlette.middleware.base import BaseHTTPMiddleware

from app.core.config import get_settings


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Comprehensive security headers middleware."""

    def __init__(self, app):
        super().__init__(app)
        self.settings = get_settings()

    async def dispatch(self, request, call_next):
        # Generate a per-request nonce for inline scripts
        nonce = base64.b64encode(os.urandom(16)).decode("utf-8")
        request.state.csp_nonce = nonce

        response = await call_next(request)

        # Basic security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"

        # Content Security Policy — nonce-based inline scripts, unsafe-inline for event handlers
        csp_policy = (
            f"default-src 'self'; "
            f"script-src 'self' 'nonce-{nonce}' https://checkout.paystack.com https://js.paystack.co https://unpkg.com https://cdn.jsdelivr.net https://cdn.tailwindcss.com; "
            f"script-src-attr 'unsafe-inline'; "
            f"style-src 'self' 'unsafe-inline' https://fonts.googleapis.com https://unpkg.com; "
            f"font-src 'self' https://fonts.gstatic.com https://unpkg.com; "
            f"img-src 'self' data: https:; "
            f"connect-src 'self' https://api.paystack.co https://checkout.paystack.com; "
            f"frame-src https://checkout.paystack.com; "
            f"object-src 'none'; "
            f"base-uri 'self';"
        )
        response.headers["Content-Security-Policy"] = csp_policy

        # HSTS (only in production with HTTPS)
        if self.settings.environment == "production" and request.url.scheme == "https":
            response.headers["Strict-Transport-Security"] = (
                "max-age=31536000; includeSubDomains"
            )

        # Additional security headers
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = (
            "geolocation=(), microphone=(), camera=()"
        )
        response.headers["Cross-Origin-Opener-Policy"] = "same-origin"

        return response


class JWTAuthMiddleware(BaseHTTPMiddleware):
    """Minimal JWT auth middleware."""

    async def dispatch(self, request, call_next):
        return await call_next(request)
