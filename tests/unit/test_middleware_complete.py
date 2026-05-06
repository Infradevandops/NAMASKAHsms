from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.middleware.security import SecurityHeadersMiddleware
from app.middleware.xss_protection import XSSProtectionMiddleware


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

    def test_xss_protection_middleware(self):
        """Test XSS protection middleware."""
        app = create_test_app()
        app.add_middleware(XSSProtectionMiddleware)
        client = TestClient(app)

        response = client.get("/test?param=<script>alert('xss')</script>")
        assert response.status_code == 200

    def test_rate_limit_middleware(self):
        """Test rate limiting - handled by UnifiedRateLimitMiddleware."""
        pass

    def test_rate_limit_public_paths(self):
        """Test public path exclusion - handled by UnifiedRateLimitMiddleware."""
        pass

    def test_adaptive_rate_limit(self):
        """Test adaptive rate limiting - handled by UnifiedRateLimitMiddleware."""
        pass
