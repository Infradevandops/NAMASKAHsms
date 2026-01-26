import asyncio
import time
from collections import defaultdict, deque
from dataclasses import dataclass
from typing import Any, Dict, Optional, Tuple

from fastapi import Request, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.config import get_settings
from app.core.logging import get_logger

logger = get_logger(__name__)


@dataclass
class RateLimitConfig:
    """Rate limit configuration."""

    requests: int
    window: int  # seconds
    burst_multiplier: float = 1.5


class TokenBucket:
    """Token bucket for smooth rate limiting."""

    def __init__(self, capacity: int, refill_rate: float):
        self.capacity = capacity
        self.refill_rate = refill_rate
        self.tokens = capacity
        self.last_refill = time.time()

    def allow_request(self) -> bool:
        """Check if request is allowed."""
        now = time.time()
        elapsed = now - self.last_refill

        # Refill tokens
        self.tokens = min(self.capacity, self.tokens + elapsed * self.refill_rate)
        self.last_refill = now

        # Check if token available
        if self.tokens >= 1:
            self.tokens -= 1
            return True
        return False

    def get_retry_after(self) -> int:
        """Get seconds until next token available."""
        if self.tokens >= 1:
            return 0
        return int((1 - self.tokens) / self.refill_rate) + 1


class UnifiedRateLimiter:
    """Unified rate limiter with multiple strategies and thread safety."""

    def __init__(self):
        self.settings = get_settings()
        self._lock = asyncio.Lock()

        # Token buckets for smooth limiting
        self.user_buckets: Dict[str, TokenBucket] = {}
        self.ip_buckets: Dict[str, TokenBucket] = {}

        # Sliding window for precise limiting
        self.ip_requests = defaultdict(deque)
        self.user_requests = defaultdict(deque)

        # System metrics for adaptive limiting
        self.request_times = deque()
        self.error_count = 0
        self.total_requests = 0

        self.last_cleanup = time.time()

        # Default limits
        self.default_config = RateLimitConfig(
            requests=getattr(self.settings, "rate_limit_requests", 100),
            window=getattr(self.settings, "rate_limit_window", 3600),
        )

        # Endpoint-specific limits
        self.endpoint_limits = {
            "/auth/login": RateLimitConfig(10, 60),  # Tighter limits for auth
            "/auth/register": RateLimitConfig(5, 3600),
            "/auth/forgot-password": RateLimitConfig(5, 3600),
            "/verify/create": RateLimitConfig(200, 3600),
            "/wallet/paystack/initialize": RateLimitConfig(50, 3600),
            "/support/submit": RateLimitConfig(10, 3600),
        }

        # Public paths excluded from rate limiting
        self.public_paths = [
            "/",
            "/app",
            "/services",
            "/pricing",
            "/about",
            "/contact",
            "/admin",
            "/docs",
            "/redoc",
            "/openapi.json",
            "/system/health",
            "/api/health",
            "/static",
            "/api/diagnostics",
        ]

    def should_skip_rate_limiting(self, path: str) -> bool:
        """Check if path should skip rate limiting."""
        return any(path.startswith(public_path) for public_path in self.public_paths)

    def get_endpoint_config(self, path: str) -> RateLimitConfig:
        """Get rate limit configuration for endpoint."""
        # Check exact match
        if path in self.endpoint_limits:
            return self.endpoint_limits[path]

        # Check prefix matches
        for endpoint_path, config in self.endpoint_limits.items():
            if path.startswith(endpoint_path):
                return config

        return self.default_config

    def get_client_ip(self, request: Request) -> str:
        """Extract client IP from request safely."""
        # Check forwarded headers (common in standard proxies)
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            # In a trusted proxy environment (like AWS ALB or Nginx), the first IP is the client
            # However, if we are behind Cloudflare, we should check CF-Connecting-IP
            return forwarded_for.split(",")[0].strip()

        cf_ip = request.headers.get("CF-Connecting-IP")
        if cf_ip:
            return cf_ip

        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip

        return request.client.host if request.client else "unknown"

    def check_token_bucket_limit(self, user_id: Optional[str], ip: str) -> Tuple[bool, int]:
        """Check rate limit using token bucket algorithm."""
        # Check IP limit - burst protection
        if ip not in self.ip_buckets:
            self.ip_buckets[ip] = TokenBucket(
                capacity=20,
                refill_rate=2.0,  # 2 request per second refill
            )

        ip_bucket = self.ip_buckets[ip]
        if not ip_bucket.allow_request():
            return False, ip_bucket.get_retry_after()

        # Check user limit if authenticated
        if user_id:
            if user_id not in self.user_buckets:
                self.user_buckets[user_id] = TokenBucket(
                    capacity=50,
                    refill_rate=5.0,  # 5 requests per second refill
                )

            user_bucket = self.user_buckets[user_id]
            if not user_bucket.allow_request():
                return False, user_bucket.get_retry_after()

        return True, 0

    def check_sliding_window_limit(
        self,
        user_id: Optional[str],
        ip: str,
        config: RateLimitConfig,
        current_time: float,
    ) -> Tuple[bool, int]:
        """Check rate limit using sliding window algorithm."""
        # Check IP limit
        ip_requests = self.ip_requests[ip]
        self._clean_old_requests(ip_requests, config.window, current_time)

        if len(ip_requests) >= config.requests:
            return False, config.window

        # Check user limit if authenticated (higher limit)
        if user_id:
            user_requests = self.user_requests[user_id]
            self._clean_old_requests(user_requests, config.window, current_time)

            user_limit = int(config.requests * 5)  # Users get 5x limit
            if len(user_requests) >= user_limit:
                return False, config.window

        return True, 0

    def _clean_old_requests(self, request_times: deque, window: int, current_time: float):
        """Remove old requests outside the window."""
        while request_times and request_times[0] <= current_time - window:
            request_times.popleft()

    def calculate_system_load(self, current_time: float) -> float:
        """Calculate system load for adaptive limiting."""
        # Clean old request times (last 5 minutes)
        while self.request_times and self.request_times[0] <= current_time - 300:
            self.request_times.popleft()

        if len(self.request_times) < 10:  # Need minimum samples
            return 0.0

        time_span = current_time - self.request_times[0]
        if time_span <= 0:
            return 0.0

        requests_per_second = len(self.request_times) / time_span
        error_rate = self.error_count / max(self.total_requests, 1)

        # High load if RPS > 100 or Error Rate > 5%
        rps_load = min(1.0, requests_per_second / 100.0)

        return max(rps_load, error_rate)

    async def check_rate_limit(
        self, request: Request, user_id: Optional[str] = None
    ) -> Tuple[bool, int, Dict[str, Any]]:
        """Check all rate limits and return result."""
        async with self._lock:
            current_time = time.time()
            ip = self.get_client_ip(request)
            path = request.url.path

            # Skip rate limiting for public paths
            if self.should_skip_rate_limiting(path):
                return True, 0, {}

            # Get endpoint configuration
            config = self.get_endpoint_config(path)

            # Check for high system load first - Adaptive Limiting
            system_load = self.calculate_system_load(current_time)
            if system_load > 0.8:  # System under high stress
                # Verify Critical endpoints are protected
                adjusted_limit = max(1, int(config.requests * 0.2))  # 80% reduction

                # Use simplified check for high load
                ip_requests_count = len(self.ip_requests[ip])
                if ip_requests_count >= adjusted_limit:
                    return (
                        False,
                        60,
                        {
                            "limit_type": "adaptive_high_load",
                            "system_load": system_load,
                            "retry_after": 60,
                        },
                    )

            # Check token bucket (for burst protection)
            bucket_allowed, bucket_retry = self.check_token_bucket_limit(user_id, ip)
            if not bucket_allowed:
                return (
                    False,
                    bucket_retry,
                    {"limit_type": "burst", "retry_after": bucket_retry},
                )

            # Check sliding window (for precise limiting)
            window_allowed, window_retry = self.check_sliding_window_limit(user_id, ip, config, current_time)
            if not window_allowed:
                return (
                    False,
                    window_retry,
                    {
                        "limit_type": "window",
                        "retry_after": window_retry,
                        "limit": config.requests,
                        "window": config.window,
                    },
                )

            # Record the request
            self.ip_requests[ip].append(current_time)
            if user_id:
                self.user_requests[user_id].append(current_time)

            self.request_times.append(current_time)
            self.total_requests += 1

            # Cleanup periodically (every 60s)
            if current_time - self.last_cleanup > 60:
                self._cleanup_old_entries(current_time)
                self.last_cleanup = current_time

            # Calculate remaining requests
            remaining = self._get_remaining_requests(user_id, ip, config, current_time)

            return (
                True,
                0,
                {
                    "limit": config.requests,
                    "remaining": remaining,
                    "reset": int(current_time + config.window),
                    "system_load": system_load,
                },
            )

    def _get_remaining_requests(
        self,
        user_id: Optional[str],
        ip: str,
        config: RateLimitConfig,
        current_time: float,
    ) -> int:
        """Get remaining requests for client."""
        if user_id:
            request_times = self.user_requests[user_id]
            effective_limit = config.requests * 5
        else:
            request_times = self.ip_requests[ip]
            effective_limit = config.requests

        # We don't clean here inside _get_remaining as it's just a view
        # Cleaning happens in check_sliding_window_limit

        # Simple count of requests in window
        window_start = current_time - config.window
        count = sum(1 for t in request_times if t > window_start)

        return max(0, effective_limit - count)

    def _cleanup_old_entries(self, current_time: float):
        """Clean up old entries to prevent memory leaks."""
        # Global max window
        max_window = 3600
        cutoff_time = current_time - max_window

        # Clean IP requests
        for ip in list(self.ip_requests.keys()):
            request_times = self.ip_requests[ip]
            while request_times and request_times[0] <= cutoff_time:
                request_times.popleft()
            if not request_times:
                del self.ip_requests[ip]  # Remove empty keys
                if ip in self.ip_buckets:
                    del self.ip_buckets[ip]

        # Clean user requests
        for user_id in list(self.user_requests.keys()):
            request_times = self.user_requests[user_id]
            while request_times and request_times[0] <= cutoff_time:
                request_times.popleft()
            if not request_times:
                del self.user_requests[user_id]
                if user_id in self.user_buckets:
                    del self.user_buckets[user_id]

    def record_error(self):
        """Record an error for adaptive limiting."""
        self.error_count += 1


class UnifiedRateLimitMiddleware(BaseHTTPMiddleware):
    """Unified rate limiting middleware."""

    def __init__(self, app):
        super().__init__(app)
        self.rate_limiter = UnifiedRateLimiter()

    async def dispatch(self, request: Request, call_next):
        """Apply unified rate limiting."""
        # Get user ID from request state (set by auth middleware)
        user_id = getattr(request.state, "user_id", None)

        # Check rate limits (async call now)
        allowed, retry_after, metadata = await self.rate_limiter.check_rate_limit(request, user_id)

        if not allowed:
            logger.warning(
                f"Rate limit exceeded for {user_id or 'anonymous'} from {self.rate_limiter.get_client_ip(request)}: {metadata}"
            )

            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={
                    "error": "Rate limit exceeded",
                    "message": f"Too many requests. Limit type: {metadata.get('limit_type', 'unknown')}",
                    "retry_after": retry_after,
                    **metadata,
                },
                headers={"Retry-After": str(retry_after)},
            )

        # Process request
        start_time = time.time()
        response = await call_next(request)
        time.time() - start_time

        # Record errors for adaptive limiting
        if response.status_code >= 500:
            self.rate_limiter.record_error()

        # Add rate limit headers
        if metadata:
            response.headers["X-RateLimit-Limit"] = str(metadata.get("limit", ""))
            response.headers["X-RateLimit-Remaining"] = str(metadata.get("remaining", ""))
            response.headers["X-RateLimit-Reset"] = str(metadata.get("reset", ""))
            response.headers["X-System-Load"] = f"{metadata.get('system_load', 0):.2f}"

        return response


# Global rate limiter instance
unified_rate_limiter = UnifiedRateLimiter()


def setup_unified_rate_limiting(app):
    """Setup unified rate limiting for FastAPI app."""
    app.add_middleware(UnifiedRateLimitMiddleware)
