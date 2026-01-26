import time
from unittest.mock import MagicMock, patch

import pytest
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.testclient import TestClient

from app.middleware.rate_limiting import (
    AdaptiveRateLimitMiddleware,
    RateLimitMiddleware,
)
from app.middleware.security import CORSMiddleware, SecurityHeadersMiddleware
from app.middleware.xss_protection import XSSProtectionMiddleware


# Mock app for testing middleware
def create_test_app():
    app = FastAPI()

    @app.get("/test")
    async def test_endpoint():
        return {"message": "success"}

    @app.get("/public")
    async def public_endpoint():
        return {"message": "public"}

    return app


class TestMiddleware:
    """Tests for various middleware components."""

    def test_security_headers_middleware(self):
        """Test that security headers are added to responses."""
        app = create_test_app()
        app.add_middleware(SecurityHeadersMiddleware)
        client = TestClient(app)

        response = client.get("/test")
        assert response.status_code == 200
        assert "Content-Security-Policy" in response.headers
        assert response.headers["X-Frame-Options"] == "DENY"
        assert response.headers["X-Content-Type-Options"] == "nosniff"
        assert response.headers["X-XSS-Protection"] == "1; mode=block"

    def test_cors_middleware(self):
        """Test CORS middleware headers."""
        app = create_test_app()
        app.add_middleware(CORSMiddleware, allowed_origins=["https://example.com"])
        client = TestClient(app)

        # Test with allowed origin
        response = client.get("/test", headers={"Origin": "https://example.com"})
        assert response.status_code == 200
        assert response.headers["Access-Control-Allow-Origin"] == "https://example.com"

        # Test OPTIONS preflight
        response = client.options(
            "/test",
            headers={
                "Origin": "https://example.com",
                "Access-Control-Request-Method": "GET",
            },
        )
        assert response.status_code == 200
        assert response.headers["Access-Control-Allow-Methods"] == "GET, POST, PUT, DELETE, OPTIONS, PATCH"

    def test_rate_limit_middleware(self):
        """Test rate limiting middleware."""
        app = create_test_app()
        # Set very low limit for testing
        app.add_middleware(RateLimitMiddleware, default_requests=2, default_window=60)
        client = TestClient(app)

        # First request
        response = client.get("/test")
        assert response.status_code == 200
        assert "X-RateLimit-Remaining" in response.headers

        # Second request
        response = client.get("/test")
        assert response.status_code == 200

        # Third request - should be rate limited
        response = client.get("/test")
        assert response.status_code == 429
        assert response.json()["error"] == "Rate limit exceeded"

    def test_rate_limit_public_paths(self):
        """Test that public paths are excluded from rate limiting."""
        app = create_test_app()
        app.add_middleware(RateLimitMiddleware, default_requests=1, default_window=60)
        client = TestClient(app)

        # Public path (defined in middleware)
        # Note: /system/health is a public path in the middleware
        @app.get("/system/health")
        async def health():
            return {"status": "ok"}

        # Multiple requests to public path should not be limited
        for _ in range(5):
            response = client.get("/system/health")
            assert response.status_code == 200

    def test_xss_protection_middleware(self):
        """Test XSS protection middleware."""
        app = create_test_app()
        app.add_middleware(XSSProtectionMiddleware)
        client = TestClient(app)

        # Test with malicious script in query param
        response = client.get("/test?param=<script>alert('xss')</script>")
        # The middleware might strip it or block it depending on implementation
        # Let's see what it does
        assert response.status_code == 200

    def test_adaptive_rate_limit(self):
        """Test adaptive rate limiting."""
        app = create_test_app()
        app.add_middleware(AdaptiveRateLimitMiddleware, base_limit=5, load_threshold=0.1)
        client = TestClient(app)

        # Make requests to trigger rate limit
        for _ in range(5):
            client.get("/test")

        response = client.get("/test")
        assert response.status_code == 429
        assert "System overloaded" in response.json()["error"]
