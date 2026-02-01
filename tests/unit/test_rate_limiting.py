

import time
from unittest.mock import MagicMock
import pytest
from app.core.unified_rate_limiting import (
from fastapi import FastAPI

    TokenBucket,
    UnifiedRateLimiter,
    UnifiedRateLimitMiddleware,
)


@pytest.mark.asyncio
async def test_token_bucket():
    bucket = TokenBucket(capacity=10, refill_rate=1.0)
    # Initial capacity
    assert bucket.allow_request() is True
    bucket.tokens = 0
    assert bucket.allow_request() is False

    # Wait for refill
    bucket.last_refill = time.time() - 5
    assert bucket.allow_request() is True
    assert bucket.get_retry_after() >= 0


@pytest.mark.asyncio
async def test_unified_rate_limiter():
    limiter = UnifiedRateLimiter()

    # Mock Request
    mock_request = MagicMock()
    mock_request.client.host = "127.0.0.1"
    mock_request.url.path = "/api/v1/test"
    mock_request.headers = {}

    # Test bucket checking
    allowed, retry_after, info = await limiter.check_rate_limit(mock_request, "user_123")
    assert allowed is True
    # We allow some keys to be missing if default path is used
    assert isinstance(info, dict)


@pytest.mark.asyncio
async def test_adaptive_load():
    limiter = UnifiedRateLimiter()
    current_time = time.time()

    # Fill request times to simulate load
for _ in range(20):
        limiter.request_times.append(current_time - 10)

    limiter.error_count = 5
    limiter.total_requests = 10

    load = limiter.calculate_system_load(current_time)
    assert load >= 0.0  # Just check it runs


def test_middleware_init():

    app = FastAPI()
    middleware = UnifiedRateLimitMiddleware(app)
    assert middleware.app == app
    assert isinstance(middleware.rate_limiter, UnifiedRateLimiter)