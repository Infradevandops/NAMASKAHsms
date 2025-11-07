"""Tests for middleware components."""
import pytest
import time
from unittest.mock import Mock, patch
from fastapi import FastAPI, Request
from fastapi.testclient import TestClient
from starlette.responses import JSONResponse

from app.middleware import (
    JWTAuthMiddleware, RateLimitMiddleware, 
    RequestLoggingMiddleware, SecurityHeadersMiddleware
)
from app.services.auth_service import AuthService
from app.models.user import User


class TestJWTAuthMiddleware:
    """Test JWT authentication middleware."""
    
    def test_excluded_paths_no_auth(self):
        """Test that excluded paths don't require authentication."""
        app = FastAPI()
        
        @app.get("/health")
        def health():
            return {"status": "ok"}
        
        app.add_middleware(JWTAuthMiddleware, exclude_paths=["/health"])
        
        client = TestClient(app)
        response = client.get("/health")
        
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}
    
    def test_missing_auth_header(self):
        """Test request without authorization header."""
        app = FastAPI()
        
        @app.get("/protected")
        def protected():
            return {"message": "protected"}
        
        app.add_middleware(JWTAuthMiddleware)
        
        client = TestClient(app)
        response = client.get("/protected")
        
        assert response.status_code == 401
        assert "Authentication required" in response.json()["error"]
    
    def test_invalid_auth_header_format(self):
        """Test request with invalid authorization header format."""
        app = FastAPI()
        
        @app.get("/protected")
        def protected():
            return {"message": "protected"}
        
        app.add_middleware(JWTAuthMiddleware)
        
        client = TestClient(app)
        response = client.get("/protected", headers={"Authorization": "Invalid token"})
        
        assert response.status_code == 401
        assert "Authentication required" in response.json()["error"]
    
    @patch('app.middleware.security.AuthService')
    def test_valid_token(self, mock_auth_service):
        """Test request with valid JWT token."""
        # Mock user
        mock_user = Mock()
        mock_user.is_active = True
        mock_user.id = "user_123"
        
        # Mock auth service
        mock_auth_instance = Mock()
        mock_auth_instance.get_user_from_token.return_value = mock_user
        mock_auth_service.return_value = mock_auth_instance
        
        app = FastAPI()
        
        @app.get("/protected")
        def protected(request: Request):
            return {"user_id": request.state.user_id}
        
        app.add_middleware(JWTAuthMiddleware)
        
        client = TestClient(app)
        response = client.get("/protected", headers={"Authorization": "Bearer valid_token"})
        
        assert response.status_code == 200
        assert response.json()["user_id"] == "user_123"
    
    @patch('app.middleware.security.AuthService')
    def test_inactive_user(self, mock_auth_service):
        """Test request with token for inactive user."""
        # Mock inactive user
        mock_user = Mock()
        mock_user.is_active = False
        
        # Mock auth service
        mock_auth_instance = Mock()
        mock_auth_instance.get_user_from_token.return_value = mock_user
        mock_auth_service.return_value = mock_auth_instance
        
        app = FastAPI()
        
        @app.get("/protected")
        def protected():
            return {"message": "protected"}
        
        app.add_middleware(JWTAuthMiddleware)
        
        client = TestClient(app)
        response = client.get("/protected", headers={"Authorization": "Bearer valid_token"})
        
        assert response.status_code == 403
        assert "Account disabled" in response.json()["error"]


class TestRateLimitMiddleware:
    """Test rate limiting middleware."""
    
    def test_under_rate_limit(self):
        """Test requests under rate limit."""
        app = FastAPI()
        
        @app.get("/test")
        def test_endpoint():
            return {"message": "ok"}
        
        # Set very high limit for this test
        app.add_middleware(RateLimitMiddleware, default_requests=100, default_window=60)
        
        client = TestClient(app)
        
        # Make several requests
        for i in range(5):
            response = client.get("/test")
            assert response.status_code == 200
            assert "X-RateLimit-Limit" in response.headers
            assert "X-RateLimit-Remaining" in response.headers
    
    def test_rate_limit_exceeded(self):
        """Test rate limit exceeded."""
        app = FastAPI()
        
        @app.get("/test")
        def test_endpoint():
            return {"message": "ok"}
        
        # Set very low limit for this test
        app.add_middleware(RateLimitMiddleware, default_requests=2, default_window=60)
        
        client = TestClient(app)
        
        # Make requests up to limit
        response1 = client.get("/test")
        assert response1.status_code == 200
        
        response2 = client.get("/test")
        assert response2.status_code == 200
        
        # This should exceed the limit
        response3 = client.get("/test")
        assert response3.status_code == 429
        assert "Rate limit exceeded" in response3.json()["error"]
    
    def test_endpoint_specific_limits(self):
        """Test endpoint-specific rate limits."""
        app = FastAPI()
        
        @app.get("/normal")
        def normal_endpoint():
            return {"message": "normal"}
        
        @app.get("/limited")
        def limited_endpoint():
            return {"message": "limited"}
        
        # Set endpoint-specific limit
        endpoint_limits = {"/limited": (1, 60)}
        app.add_middleware(
            RateLimitMiddleware, 
            default_requests=10, 
            default_window=60,
            endpoint_limits=endpoint_limits
        )
        
        client = TestClient(app)
        
        # Normal endpoint should work multiple times
        response1 = client.get("/normal")
        assert response1.status_code == 200
        
        response2 = client.get("/normal")
        assert response2.status_code == 200
        
        # Limited endpoint should work once
        response3 = client.get("/limited")
        assert response3.status_code == 200
        
        # Second request to limited endpoint should fail
        response4 = client.get("/limited")
        assert response4.status_code == 429


class TestRequestLoggingMiddleware:
    """Test request logging middleware."""
    
    @patch('app.middleware.logging.logger')
    def test_request_logging(self, mock_logger):
        """Test that requests are logged."""
        app = FastAPI()
        
        @app.get("/test")
        def test_endpoint():
            return {"message": "ok"}
        
        app.add_middleware(RequestLoggingMiddleware)
        
        client = TestClient(app)
        response = client.get("/test")
        
        assert response.status_code == 200
        assert "X-Process-Time" in response.headers
        
        # Check that logging was called
        assert mock_logger.info.called
    
    def test_excluded_paths_not_logged(self):
        """Test that excluded paths are not logged."""
        app = FastAPI()
        
        @app.get("/health")
        def health():
            return {"status": "ok"}
        
        app.add_middleware(RequestLoggingMiddleware, exclude_paths=["/health"])
        
        with patch('app.middleware.logging.logger') as mock_logger:
            client = TestClient(app)
            response = client.get("/health")
            
            assert response.status_code == 200
            # Should not have logged anything
            assert not mock_logger.info.called
    
    @patch('app.middleware.logging.logger')
    def test_error_response_logging(self, mock_logger):
        """Test that error responses are logged appropriately."""
        app = FastAPI()
        
        @app.get("/error")
        def error_endpoint():
            return JSONResponse(status_code=500, content={"error": "server error"})
        
        app.add_middleware(RequestLoggingMiddleware)
        
        client = TestClient(app)
        response = client.get("/error")
        
        assert response.status_code == 500
        
        # Check that error was logged
        assert mock_logger.error.called


class TestSecurityHeadersMiddleware:
    """Test security headers middleware."""
    
    def test_security_headers_added(self):
        """Test that security headers are added to responses."""
        app = FastAPI()
        
        @app.get("/test")
        def test_endpoint():
            return {"message": "ok"}
        
        app.add_middleware(SecurityHeadersMiddleware)
        
        client = TestClient(app)
        response = client.get("/test")
        
        assert response.status_code == 200
        
        # Check security headers
        assert "Content-Security-Policy" in response.headers
        assert "X-Content-Type-Options" in response.headers
        assert "X-Frame-Options" in response.headers
        assert "X-XSS-Protection" in response.headers
        assert "Referrer-Policy" in response.headers
        
        # Check header values
        assert response.headers["X-Content-Type-Options"] == "nosniff"
        assert response.headers["X-Frame-Options"] == "DENY"
        assert response.headers["X-XSS-Protection"] == "1; mode=block"
    
    def test_csp_header_content(self):
        """Test Content Security Policy header content."""
        app = FastAPI()
        
        @app.get("/test")
        def test_endpoint():
            return {"message": "ok"}
        
        app.add_middleware(SecurityHeadersMiddleware)
        
        client = TestClient(app)
        response = client.get("/test")
        
        csp = response.headers["Content-Security-Policy"]
        
        # Check that CSP includes expected directives
        assert "default-src 'self'" in csp
        assert "script-src" in csp
        assert "style-src" in csp
        assert "img-src" in csp


class TestMiddlewareIntegration:
    """Test middleware integration and order."""
    
    def test_multiple_middleware_order(self):
        """Test that multiple middleware work together in correct order."""
        app = FastAPI()
        
        @app.get("/test")
        def test_endpoint():
            return {"message": "ok"}
        
        # Add middleware in specific order
        app.add_middleware(SecurityHeadersMiddleware)
        app.add_middleware(RequestLoggingMiddleware, exclude_paths=[])
        app.add_middleware(RateLimitMiddleware, default_requests=10, default_window=60)
        
        client = TestClient(app)
        response = client.get("/test")
        
        assert response.status_code == 200
        
        # Check that all middleware added their headers/effects
        assert "X-Process-Time" in response.headers  # From logging middleware
        assert "X-RateLimit-Limit" in response.headers  # From rate limit middleware
        assert "X-Content-Type-Options" in response.headers  # From security middleware
    
    @patch('app.middleware.security.AuthService')
    def test_auth_and_rate_limit_integration(self, mock_auth_service):
        """Test authentication and rate limiting working together."""
        # Mock user
        mock_user = Mock()
        mock_user.is_active = True
        mock_user.id = "user_123"
        
        # Mock auth service
        mock_auth_instance = Mock()
        mock_auth_instance.get_user_from_token.return_value = mock_user
        mock_auth_service.return_value = mock_auth_instance
        
        app = FastAPI()
        
        @app.get("/protected")
        def protected_endpoint(request: Request):
            return {"user_id": request.state.user_id}
        
        # Add both middleware
        app.add_middleware(RateLimitMiddleware, default_requests=5, default_window=60)
        app.add_middleware(JWTAuthMiddleware, exclude_paths=[])
        
        client = TestClient(app)
        
        # Make authenticated request
        response = client.get("/protected", headers={"Authorization": "Bearer valid_token"})
        
        assert response.status_code == 200
        assert response.json()["user_id"] == "user_123"
        
        # Check that both middleware added their headers
        assert "X-RateLimit-Limit" in response.headers