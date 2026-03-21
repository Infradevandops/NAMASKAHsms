"""Monitoring middleware for collecting metrics.

Tracks:
- Request latency
- Error rates
- Active requests
- Tier identification metrics
"""

import logging
import time

from fastapi import Request

from app.core.metrics import (
    set_active_requests,
    track_api_request,
    track_cache_hit,
    track_tier_identification,
)

logger = logging.getLogger(__name__)

# Track active requests
active_request_count = 0


async def monitoring_middleware(request: Request, call_next):
    """Middleware to track request metrics."""
    global active_request_count

    # Increment active requests
    active_request_count += 1
    set_active_requests(active_request_count)

    # Record start time
    start_time = time.time()

    try:
        # Process request
        response = await call_next(request)

        # Calculate duration
        duration = time.time() - start_time

        # Extract endpoint
        endpoint = request.url.path
        method = request.method

        # Track metrics
        track_api_request(method, endpoint, response.status_code, duration)

        # Log slow requests
        if duration > 1.0:
            logger.warning(f"Slow request: {method} {endpoint} took {duration:.2f}s")

        return response

    except Exception as e:
        # Calculate duration
        duration = time.time() - start_time

        # Extract endpoint
        endpoint = request.url.path
        method = request.method

        # Track error
        track_api_request(method, endpoint, 500, duration)

        logger.error(
            f"Request error: {method} {endpoint} - {type(e).__name__}: {str(e)}"
        )

        raise

    finally:
        # Decrement active requests
        active_request_count -= 1
        set_active_requests(active_request_count)


async def tier_monitoring_middleware(request: Request, call_next):
    """Middleware to track tier identification metrics."""
    # Check if this is a tier-related request
    if "/tier" in request.url.path or "/verify" in request.url.path:
        start_time = time.time()

        try:
            response = await call_next(request)
            duration = time.time() - start_time

            # Track tier identification latency
            if duration < 1.0:  # Only track successful requests
                logger.debug(
                    f"Tier identification: {request.url.path} took {duration:.3f}s"
                )

            return response

        except Exception as e:
            duration = time.time() - start_time
            logger.error(
                f"Tier identification error: {request.url.path} - {type(e).__name__}"
            )
            raise

    return await call_next(request)


async def cache_monitoring_middleware(request: Request, call_next):
    """Middleware to track cache metrics."""
    # Check if cache headers are present
    if "X-Cache-Hit" in request.headers:
        cache_hit = request.headers.get("X-Cache-Hit") == "true"
        track_cache_hit(cache_hit)

    response = await call_next(request)

    # Add cache status to response headers
    if hasattr(request.state, "cache_hit"):
        response.headers["X-Cache-Hit"] = str(request.state.cache_hit).lower()

    return response
