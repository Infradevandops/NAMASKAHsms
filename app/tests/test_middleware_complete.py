"""Complete middleware tests for task 5.4."""
from unittest.mock import Mock, patch
from fastapi import FastAPI, Request

from app.middleware.security import JWTAuthMiddleware, APIKeyAuthMiddleware


class TestJWTAuthMiddleware:
    """Test JWT authentication middleware."""

    def test_excluded_paths(self):
        """Test excluded paths bypass authentication."""
        app = FastAPI()

        @app.get("/health")
        def health():
            return {"status": "ok"}

        app.add_middleware(JWTAuthMiddleware, exclude_paths=["/health"])
        client = TestClient(app)

        response = client.get("/health")
        assert response.status_code == 200

    def test_missing_token(self):
        """Test missing authorization header."""
        app = FastAPI()

        @app.get("/protected")
        def protected():
            return {"data": "secret"}

        app.add_middleware(JWTAuthMiddleware)
        client = TestClient(app)

        response = client.get("/protected")
        assert response.status_code == 401

    @patch('app.services.auth_service.AuthService')
    def test_valid_token(self, mock_auth):
        """Test valid JWT token."""
        mock_user = Mock()
        mock_user.is_active = True
        mock_user.id = "user_123"

        mock_auth_instance = Mock()
        mock_auth_instance.get_user_from_token.return_value = mock_user
        mock_auth.return_value = mock_auth_instance

        app = FastAPI()

        @app.get("/protected")
        def protected(request: Request):
            return {"user_id": request.state.user_id}

        app.add_middleware(JWTAuthMiddleware)
        client = TestClient(app)

        response = client.get("/protected", headers={"Authorization": "Bearer valid_token"})
        assert response.status_code == 200


class TestAPIKeyAuthMiddleware:
    """Test API key authentication middleware."""

    @patch('app.services.auth_service.AuthService')
    def test_valid_api_key(self, mock_auth):
        """Test valid API key authentication."""
        mock_user = Mock()
        mock_user.is_active = True
        mock_user.id = "user_123"

        mock_auth_instance = Mock()
        mock_auth_instance.verify_api_key.return_value = mock_user
        mock_auth.return_value = mock_auth_instance

        app = FastAPI()

        @app.get("/api/data")
        def api_data(request: Request):
            return {"user_id": request.state.user_id}

        app.add_middleware(APIKeyAuthMiddleware)
        client = TestClient(app)

        response = client.get("/api/data", headers={"X - API-Key": "nsk_valid_key"})
        assert response.status_code == 200

    def test_invalid_api_key(self):
        """Test invalid API key."""
        app = FastAPI()

        @app.get("/api/data")
        def api_data():
            return {"data": "secret"}

        app.add_middleware(APIKeyAuthMiddleware)
        client = TestClient(app)

        response = client.get("/api/data", headers={"X - API-Key": "invalid_key"})
        assert response.status_code == 401


class TestRateLimitMiddleware:
    """Test rate limiting middleware."""

    def test_under_limit(self):
        """Test requests under rate limit."""
        app = FastAPI()

        @app.get("/test")
        def test_endpoint():
            return {"message": "ok"}

        app.add_middleware(RateLimitMiddleware, default_requests=100, default_window=60)
        client = TestClient(app)

        response = client.get("/test")
        assert response.status_code == 200
        assert "X - RateLimit-Limit" in response.headers

    def test_rate_limit_exceeded(self):
        """Test rate limit exceeded."""
        app = FastAPI()

        @app.get("/test")
        def test_endpoint():
            return {"message": "ok"}

        app.add_middleware(RateLimitMiddleware, default_requests=1, default_window=60)
        client = TestClient(app)

        # First request succeeds
        response1 = client.get("/test")
        assert response1.status_code == 200

        # Second request should be rate limited
        response2 = client.get("/test")
        assert response2.status_code == 429


class TestRequestLoggingMiddleware:
    """Test request logging middleware."""

    @patch('app.middleware.logging.logger')
    def test_request_logging(self, mock_logger):
        """Test request logging functionality."""
        app = FastAPI()

        @app.get("/test")
        def test_endpoint():
            return {"message": "ok"}

        app.add_middleware(RequestLoggingMiddleware)
        client = TestClient(app)

        response = client.get("/test")
        assert response.status_code == 200
        assert "X - Process-Time" in response.headers
        mock_logger.info.assert_called()

    def test_excluded_paths(self):
        """Test excluded paths are not logged."""
        app = FastAPI()

        @app.get("/health")
        def health():
            return {"status": "ok"}

        app.add_middleware(RequestLoggingMiddleware, exclude_paths=["/health"])

        with patch('app.middleware.logging.logger') as mock_logger:
            client = TestClient(app)
            response = client.get("/health")

            assert response.status_code == 200
            assert not mock_logger.info.called


class TestMiddlewareIntegration:
    """Test middleware integration."""

    def test_multiple_middleware_order(self):
        """Test multiple middleware work together."""
        app = FastAPI()

        @app.get("/test")
        def test_endpoint():
            return {"message": "ok"}

        app.add_middleware(RequestLoggingMiddleware)
        app.add_middleware(RateLimitMiddleware, default_requests=10, default_window=60)

        client = TestClient(app)
        response = client.get("/test")

        assert response.status_code == 200
        assert "X - Process-Time" in response.headers
        assert "X - RateLimit-Limit" in response.headers
