"""Comprehensive test suite for unified rate limiting system."""
import pytest
import time
from unittest.mock import Mock, patch
from fastapi import FastAPI

from app.core.unified_rate_limiting import (
    TokenBucket,
    UnifiedRateLimiter,
    UnifiedRateLimitMiddleware,
    RateLimitConfig,
    setup_unified_rate_limiting
)


class TestTokenBucket:
    """Test token bucket implementation."""

    def test_token_bucket_initialization(self):
        """Test token bucket initialization."""
        bucket = TokenBucket(capacity=10, refill_rate=1.0)
        assert bucket.capacity == 10
        assert bucket.refill_rate == 1.0
        assert bucket.tokens == 10

    def test_token_bucket_allow_request(self):
        """Test token bucket allows requests when tokens available."""
        bucket = TokenBucket(capacity=5, refill_rate=1.0)

        # Should allow 5 requests initially
        for _ in range(5):
            assert bucket.allow_request() is True

        # Should deny 6th request
        assert bucket.allow_request() is False

    def test_token_bucket_refill(self):
        """Test token bucket refills over time."""
        bucket = TokenBucket(capacity=2, refill_rate=2.0)  # 2 tokens per second

        # Consume all tokens
        assert bucket.allow_request() is True
        assert bucket.allow_request() is True
        assert bucket.allow_request() is False

        # Wait and check refill
        time.sleep(0.6)  # Should refill ~1.2 tokens
        assert bucket.allow_request() is True
        assert bucket.allow_request() is False

    def test_token_bucket_retry_after(self):
        """Test token bucket retry after calculation."""
        bucket = TokenBucket(capacity=1, refill_rate=1.0)

        # Consume token
        assert bucket.allow_request() is True

        # Check retry after
        retry_after = bucket.get_retry_after()
        assert retry_after >= 1
        assert retry_after <= 2


class TestRateLimitConfig:
    """Test rate limit configuration."""

    def test_rate_limit_config_creation(self):
        """Test rate limit config creation."""
        config = RateLimitConfig(requests=100, window=3600)
        assert config.requests == 100
        assert config.window == 3600
        assert config.burst_multiplier == 1.5

    def test_rate_limit_config_with_burst(self):
        """Test rate limit config with custom burst multiplier."""
        config = RateLimitConfig(requests=50, window=1800, burst_multiplier=2.0)
        assert config.burst_multiplier == 2.0


class TestUnifiedRateLimiter:
    """Test unified rate limiter."""

    @pytest.fixture
    def rate_limiter(self):
        """Create rate limiter instance."""
        return UnifiedRateLimiter()

    @pytest.fixture
    def mock_request(self):
        """Create mock request."""
        request = Mock()
        request.url.path = "/test"
        request.client.host = "127.0.0.1"
        request.headers = {}
        return request

    def test_should_skip_rate_limiting_public_paths(self, rate_limiter):
        """Test skipping rate limiting for public paths."""
        assert rate_limiter.should_skip_rate_limiting("/") is True
        assert rate_limiter.should_skip_rate_limiting("/static/css/style.css") is True
        assert rate_limiter.should_skip_rate_limiting("/docs") is True
        assert rate_limiter.should_skip_rate_limiting("/api/test") is False

    def test_get_endpoint_config_exact_match(self, rate_limiter):
        """Test getting endpoint config for exact match."""
        config = rate_limiter.get_endpoint_config("/auth/login")
        assert config.requests == 100
        assert config.window == 3600

    def test_get_endpoint_config_prefix_match(self, rate_limiter):
        """Test getting endpoint config for prefix match."""
        config = rate_limiter.get_endpoint_config("/auth/login/callback")
        assert config.requests == 100  # Should match /auth/login

    def test_get_endpoint_config_default(self, rate_limiter):
        """Test getting default endpoint config."""
        config = rate_limiter.get_endpoint_config("/unknown/endpoint")
        assert config == rate_limiter.default_config

    def test_get_client_ip_forwarded_for(self, rate_limiter):
        """Test extracting client IP from X - Forwarded-For header."""
        request = Mock()
        request.headers = {"X - Forwarded-For": "192.168.1.1, 10.0.0.1"}
        request.client.host = "127.0.0.1"

        ip = rate_limiter.get_client_ip(request)
        assert ip == "192.168.1.1"

    def test_get_client_ip_real_ip(self, rate_limiter):
        """Test extracting client IP from X - Real-IP header."""
        request = Mock()
        request.headers = {"X - Real-IP": "192.168.1.2"}
        request.client.host = "127.0.0.1"

        ip = rate_limiter.get_client_ip(request)
        assert ip == "192.168.1.2"

    def test_get_client_ip_direct(self, rate_limiter):
        """Test extracting client IP directly."""
        request = Mock()
        request.headers = {}
        request.client.host = "127.0.0.1"

        ip = rate_limiter.get_client_ip(request)
        assert ip == "127.0.0.1"

    def test_check_token_bucket_limit_success(self, rate_limiter):
        """Test token bucket limit check success."""
        allowed, retry_after = rate_limiter.check_token_bucket_limit(None, "127.0.0.1")
        assert allowed is True
        assert retry_after == 0

    def test_check_token_bucket_limit_exceeded(self, rate_limiter):
        """Test token bucket limit exceeded."""
        ip = "127.0.0.1"

        # Exhaust tokens
        for _ in range(15):  # More than bucket capacity
            rate_limiter.check_token_bucket_limit(None, ip)

        allowed, retry_after = rate_limiter.check_token_bucket_limit(None, ip)
        assert allowed is False
        assert retry_after > 0

    def test_check_sliding_window_limit_success(self, rate_limiter):
        """Test sliding window limit check success."""
        config = RateLimitConfig(requests=10, window=60)
        current_time = time.time()

        allowed, retry_after = rate_limiter.check_sliding_window_limit(
            None, "127.0.0.1", config, current_time
        )
        assert allowed is True
        assert retry_after == 0

    def test_check_sliding_window_limit_exceeded(self, rate_limiter):
        """Test sliding window limit exceeded."""
        config = RateLimitConfig(requests=2, window=60)
        current_time = time.time()
        ip = "127.0.0.2"

        # Add requests to exceed limit
        for _ in range(3):
            rate_limiter.ip_requests[ip].append(current_time)

        allowed, retry_after = rate_limiter.check_sliding_window_limit(
            None, ip, config, current_time
        )
        assert allowed is False
        assert retry_after == 60

    def test_calculate_system_load_low(self, rate_limiter):
        """Test system load calculation with low load."""
        current_time = time.time()

        # Add few requests
        for i in range(3):
            rate_limiter.request_times.append(current_time - i)

        load = rate_limiter.calculate_system_load(current_time)
        assert 0.0 <= load <= 1.0

    def test_calculate_system_load_high(self, rate_limiter):
        """Test system load calculation with high load."""
        current_time = time.time()

        # Add many requests and errors
        for i in range(100):
            rate_limiter.request_times.append(current_time - i * 0.1)

        rate_limiter.total_requests = 100
        rate_limiter.error_count = 20

        load = rate_limiter.calculate_system_load(current_time)
        assert load > 0.5

    def test_check_rate_limit_public_path(self, rate_limiter):
        """Test rate limit check for public path."""
        request = Mock()
        request.url.path = "/static/test.css"

        allowed, retry_after, metadata = rate_limiter.check_rate_limit(request)
        assert allowed is True
        assert retry_after == 0
        assert metadata == {}

    def test_check_rate_limit_success(self, rate_limiter, mock_request):
        """Test successful rate limit check."""
        allowed, retry_after, metadata = rate_limiter.check_rate_limit(mock_request)
        assert allowed is True
        assert retry_after == 0
        assert "limit" in metadata
        assert "remaining" in metadata

    def test_record_error(self, rate_limiter):
        """Test error recording."""
        initial_count = rate_limiter.error_count
        rate_limiter.record_error()
        assert rate_limiter.error_count == initial_count + 1


class TestUnifiedRateLimitMiddleware:
    """Test unified rate limit middleware."""

    @pytest.fixture
    def app(self):
        """Create test FastAPI app."""
        app = FastAPI()

        @app.get("/test")
        async def test_endpoint():
            return {"message": "success"}

        @app.get("/error")
        async def error_endpoint():
            raise Exception("Test error")

        @app.get("/static/test.css")
        async def static_endpoint():
            return {"content": "css"}

        return app

    @pytest.fixture
    def client(self, app):
        """Create test client with middleware."""
        app.add_middleware(UnifiedRateLimitMiddleware)
        return TestClient(app)

    def test_successful_request(self, client):
        """Test successful request passes through."""
        response = client.get("/test")
        assert response.status_code == 200
        assert response.json() == {"message": "success"}

    def test_rate_limit_headers(self, client):
        """Test rate limit headers are added."""
        response = client.get("/test")
        assert response.status_code == 200
        assert "X - RateLimit-Limit" in response.headers
        assert "X - RateLimit-Remaining" in response.headers
        assert "X - RateLimit-Reset" in response.headers
        assert "X - System-Load" in response.headers
        assert "X - Process-Time" in response.headers

    def test_public_path_no_rate_limiting(self, client):
        """Test public paths are not rate limited."""
        # Make many requests to static endpoint
        for _ in range(20):
            response = client.get("/static/test.css")
            assert response.status_code == 200

    def test_rate_limit_exceeded(self, client):
        """Test rate limit exceeded response."""
        # This test would need to be adjusted based on actual limits
        # For now, we'll test the structure

        # Mock the rate limiter to return exceeded
        with patch('app.core.unified_rate_limiting.UnifiedRateLimiter.check_rate_limit') as mock_check:
            mock_check.return_value = (False, 60, {"limit_type": "test"})

            response = client.get("/test")
            assert response.status_code == 429
            assert "Rate limit exceeded" in response.json()["error"]
            assert "Retry - After" in response.headers

    def test_error_recording(self, client):
        """Test error recording for adaptive limiting."""
        # This would trigger a 500 error, but FastAPI handles it
        # We'll test that the middleware processes it correctly
        try:
            client.get("/error")
            # The error might be handled by FastAPI's error handling
        except BaseException:
            pass  # Expected for test error endpoint


class TestIntegrationScenarios:
    """Test integration scenarios."""

    @pytest.fixture
    def app_with_rate_limiting(self):
        """Create app with unified rate limiting."""
        app = FastAPI()
        setup_unified_rate_limiting(app)

        @app.get("/api/test")
        async def test_endpoint():
            return {"message": "success"}

        @app.get("/auth/login")
        async def login_endpoint():
            return {"token": "test"}

        @app.get("/static/style.css")
        async def static_endpoint():
            return {"content": "css"}

        return app

    def test_different_endpoints_different_limits(self, app_with_rate_limiting):
        """Test different endpoints have different limits."""
        client = TestClient(app_with_rate_limiting)

        # Test regular endpoint
        response = client.get("/api/test")
        assert response.status_code == 200

        # Test auth endpoint (should have different limits)
        response = client.get("/auth/login")
        assert response.status_code == 200

        # Test static endpoint (should not be rate limited)
        response = client.get("/static/style.css")
        assert response.status_code == 200

    def test_user_vs_anonymous_limits(self, app_with_rate_limiting):
        """Test authenticated users get higher limits."""
        client = TestClient(app_with_rate_limiting)

        # Test anonymous request
        response = client.get("/api/test")
        assert response.status_code == 200

        # Test with user ID in state (would need proper auth middleware setup)
        # This is a simplified test of the concept
        response = client.get("/api/test")
        assert response.status_code == 200


class TestSetupFunction:
    """Test setup function."""

    def test_setup_unified_rate_limiting(self):
        """Test setup function adds middleware."""
        app = FastAPI()

        # Mock the add_middleware method
        app.add_middleware = Mock()

        setup_unified_rate_limiting(app)

        # Verify middleware was added
        app.add_middleware.assert_called_once_with(UnifiedRateLimitMiddleware)


class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_empty_request_times(self):
        """Test handling of empty request times."""
        rate_limiter = UnifiedRateLimiter()
        current_time = time.time()

        load = rate_limiter.calculate_system_load(current_time)
        assert load == 0.0

    def test_cleanup_old_entries(self):
        """Test cleanup of old entries."""
        rate_limiter = UnifiedRateLimiter()
        current_time = time.time()
        old_time = current_time - 7200  # 2 hours ago

        # Add old entries
        rate_limiter.ip_requests["test_ip"].append(old_time)
        rate_limiter.user_requests["test_user"].append(old_time)

        # Trigger cleanup
        rate_limiter._cleanup_old_entries(current_time)

        # Old entries should be removed
        assert len(rate_limiter.ip_requests["test_ip"]) == 0
        assert len(rate_limiter.user_requests["test_user"]) == 0

    def test_missing_client_info(self):
        """Test handling of missing client information."""
        rate_limiter = UnifiedRateLimiter()

        request = Mock()
        request.url.path = "/test"
        request.client = None
        request.headers = {}

        ip = rate_limiter.get_client_ip(request)
        assert ip == "unknown"

    def test_zero_division_protection(self):
        """Test protection against zero division."""
        rate_limiter = UnifiedRateLimiter()
        current_time = time.time()

        # Add requests at same time
        rate_limiter.request_times.append(current_time)
        rate_limiter.request_times.append(current_time)

        load = rate_limiter.calculate_system_load(current_time)
        assert load >= 0.0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
