"""Security middleware - comprehensive security headers."""

import base64
import os

from starlette.datastructures import MutableHeaders
from starlette.types import ASGIApp, Receive, Scope, Send

from app.core.config import get_settings


class SecurityHeadersMiddleware:
    """Pure ASGI security headers middleware.

    Replaces BaseHTTPMiddleware to avoid the WebSocket crash:
    BaseHTTPMiddleware intercepts all ASGI scopes including websocket,
    corrupting the message sequence and causing RuntimeError on accept().
    """

    def __init__(self, app: ASGIApp):
        self.app = app
        self.settings = get_settings()

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        # Generate per-request nonce and attach to request.state
        nonce = base64.b64encode(os.urandom(16)).decode("utf-8")
        if "state" not in scope:
            scope["state"] = {}
        scope["state"]["csp_nonce"] = nonce

        is_production = self.settings.environment == "production"
        is_testing = self.settings.environment == "testing"

        csp_policy = (
            f"default-src 'self'; "
            f"script-src 'self' 'nonce-{nonce}' https://checkout.paystack.com "
            f"https://js.paystack.co https://unpkg.com https://cdn.jsdelivr.net "
            f"https://cdn.tailwindcss.com https://cdnjs.cloudflare.com"
        )

        if is_testing:
            csp_policy += " 'unsafe-eval'"

        csp_policy += (
            "; script-src-attr 'unsafe-inline'; "
            "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com "
            "https://unpkg.com; font-src 'self' https://fonts.gstatic.com "
            "https://unpkg.com; img-src 'self' data: https: "
            "https://cdn.simpleicons.org; connect-src 'self' "
            "https://api.paystack.co https://checkout.paystack.com "
            "https://min-api.cryptocompare.com; "
            "frame-src https://checkout.paystack.com; object-src 'none'; "
            "base-uri 'self';"
        )


        async def send_with_headers(message: dict) -> None:
            if message["type"] == "http.response.start":
                headers = MutableHeaders(scope=message)
                headers["X-Content-Type-Options"] = "nosniff"
                headers["X-Frame-Options"] = "DENY"
                headers["X-XSS-Protection"] = "1; mode=block"
                headers["Content-Security-Policy"] = csp_policy
                headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
                headers["Permissions-Policy"] = (
                    "geolocation=(), microphone=(), camera=()"
                )
                headers["Cross-Origin-Opener-Policy"] = "same-origin"
                if is_production:
                    headers["Strict-Transport-Security"] = (
                        "max-age=31536000; includeSubDomains"
                    )
            await send(message)

        await self.app(scope, receive, send_with_headers)


class JWTAuthMiddleware:
    """Minimal JWT auth middleware."""

    def __init__(self, app: ASGIApp):
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        await self.app(scope, receive, send)
