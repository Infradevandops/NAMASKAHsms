"""Rate limiting middleware with configurable limits per endpoint."""

import time
from collections import defaultdict, deque
from typing import Dict, Optional, Tuple

from fastapi import Request, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from app.core.config import settings


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Rate limiting middleware with IP - based and user - based strategies."""

    def __init__(
        self,
        app,
        default_requests: int = None,
        default_window: int = None,  # 1 hour
        endpoint_limits: Optional[Dict[str, Tuple[int, int]]] = None,
    ):
        super().__init__(app)
        # Use configured defaults if not explicitly provided
        self.default_requests = default_requests or settings.rate_limit_requests
        self.default_window = default_window or settings.rate_limit_window
        self.endpoint_limits = endpoint_limits or {}

        # Storage for rate limit data
        self.ip_requests = defaultdict(deque)
        self.user_requests = defaultdict(deque)

        # Endpoint - specific limits
        self.endpoint_limits.update(
            {
                "/auth/login": (100, 3600),  # 100 requests per hour (industry standard)
                "/auth/register": (20, 3600),  # 20 registrations per hour
                "/auth/forgot - password": (10, 3600),  # 10 password resets per hour
                "/verify/create": (200, 3600),  # 200 verifications per hour
                "/wallet/paystack/initialize": (50, 3600),  # 50 payments per hour
                "/support/submit": (10, 3600),  # 10 support tickets per hour
            }
        )

    async def dispatch(self, request: Request, call_next):
        """Apply rate limiting based on IP and user."""

        # Exclude public pages from rate limiting
        public_paths = [
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
            "/static",  # Static files
        ]

        # Skip rate limiting for public pages
        if any(request.url.path.startswith(path) for path in public_paths):
            return await call_next(request)

        current_time = time.time()

        # Get client identifier
        client_ip = self._get_client_ip(request)
        user_id = getattr(request.state, "user_id", None)

        # Get rate limit for this endpoint
        requests_limit, window = self._get_endpoint_limit(request.url.path)

        # Check IP - based rate limit
        if not self._check_rate_limit(
            self.ip_requests[client_ip], requests_limit, window, current_time
        ):
            return self._create_rate_limit_response("IP rate limit exceeded")

        # Check user - based rate limit (if authenticated)
        if user_id:
            user_limit = requests_limit * 2  # Users get higher limits
            if not self._check_rate_limit(
                self.user_requests[user_id], user_limit, window, current_time
            ):
                return self._create_rate_limit_response("User rate limit exceeded")

        # Record the request
        self.ip_requests[client_ip].append(current_time)
        if user_id:
            self.user_requests[user_id].append(current_time)

        # Clean old entries periodically
        if int(current_time) % 60 == 0:  # Every minute
            self._cleanup_old_entries(current_time)

        response = await call_next(request)

        # Add rate limit headers
        remaining = self._get_remaining_requests(
            client_ip, user_id, requests_limit, window, current_time
        )
        reset_time = int(current_time + window)

        response.headers["X - RateLimit-Limit"] = str(requests_limit)
        response.headers["X - RateLimit-Remaining"] = str(remaining)
        response.headers["X - RateLimit-Reset"] = str(reset_time)

        return response

    @staticmethod
    def _get_client_ip(request: Request) -> str:
        """Get client IP address from request."""
        # Check for forwarded headers (for reverse proxies)
        forwarded_for = request.headers.get("X - Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()

        real_ip = request.headers.get("X - Real-IP")
        if real_ip:
            return real_ip

        # Fallback to direct client IP
        return request.client.host if request.client else "unknown"

    def _get_endpoint_limit(self, path: str) -> Tuple[int, int]:
        """Get rate limit for specific endpoint."""
        # Check exact path match
        if path in self.endpoint_limits:
            return self.endpoint_limits[path]

        # Check prefix matches
        for endpoint_path, limit in self.endpoint_limits.items():
            if path.startswith(endpoint_path):
                return limit

        # Return default limit
        return self.default_requests, self.default_window

    @staticmethod
    def _check_rate_limit(
        request_times: deque, limit: int, window: int, current_time: float
    ) -> bool:
        """Check if request is within rate limit."""
        # Remove old requests outside the window
        while request_times and request_times[0] <= current_time - window:
            request_times.popleft()

        # Check if under limit
        return len(request_times) < limit

    def _get_remaining_requests(
        self,
        client_ip: str,
        user_id: Optional[str],
        limit: int,
        window: int,
        current_time: float,
    ) -> int:
        """Get remaining requests for client."""
        # Use user - based limit if authenticated, otherwise IP - based
        if user_id:
            request_times = self.user_requests[user_id]
            effective_limit = limit * 2
        else:
            request_times = self.ip_requests[client_ip]
            effective_limit = limit

        # Remove old requests
        while request_times and request_times[0] <= current_time - window:
            request_times.popleft()

        return max(0, effective_limit - len(request_times))

    def _cleanup_old_entries(self, current_time: float):
        """Clean up old entries to prevent memory leaks."""
        max_window = max(
            self.default_window,
            max((w for _, w in self.endpoint_limits.values()), default=0),
        )
        cutoff_time = current_time - max_window

        # Clean IP requests
        for ip in list(self.ip_requests.keys()):
            request_times = self.ip_requests[ip]
            while request_times and request_times[0] <= cutoff_time:
                request_times.popleft()

            # Remove empty entries
            if not request_times:
                del self.ip_requests[ip]

        # Clean user requests
        for user_id in list(self.user_requests.keys()):
            request_times = self.user_requests[user_id]
            while request_times and request_times[0] <= cutoff_time:
                request_times.popleft()

            # Remove empty entries
            if not request_times:
                del self.user_requests[user_id]

    def _create_rate_limit_response(self, message: str) -> JSONResponse:
        """Create rate limit exceeded response."""
        return JSONResponse(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            content={
                "error": "Rate limit exceeded",
                "message": message,
                "retry_after": self.default_window,
            },
            headers={"Retry - After": str(self.default_window)},
        )


class AdaptiveRateLimitMiddleware(BaseHTTPMiddleware):
    """Adaptive rate limiting that adjusts based on system load."""

    def __init__(self, app, base_limit: int = 100, load_threshold: float = 0.8):
        super().__init__(app)
        self.base_limit = base_limit
        self.load_threshold = load_threshold
        self.request_times = deque()
        self.error_count = 0
        self.total_requests = 0

    async def dispatch(self, request: Request, call_next):
        """Apply adaptive rate limiting."""
        current_time = time.time()

        # Calculate current system load (simplified)
        system_load = self._calculate_system_load(current_time)

        # Adjust rate limit based on load
        if system_load > self.load_threshold:
            adjusted_limit = int(self.base_limit * 0.5)  # Reduce by 50%
        else:
            adjusted_limit = self.base_limit

        # Apply rate limiting

        # Simple rate limiting logic
        self.request_times.append(current_time)

        # Remove old requests (last minute)
        while self.request_times and self.request_times[0] <= current_time - 60:
            self.request_times.popleft()

        # Check if over limit
        if len(self.request_times) > adjusted_limit:
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={
                    "error": "System overloaded",
                    "message": "Rate limit reduced due to high system load",
                    "current_limit": adjusted_limit,
                },
            )

        # Process request
        start_time = time.time()
        response = await call_next(request)
        process_time = time.time() - start_time

        # Track metrics
        self.total_requests += 1
        if response.status_code >= 500:
            self.error_count += 1

        # Add performance headers
        response.headers["X - Process-Time"] = f"{process_time:.3f}"
        response.headers["X - System-Load"] = f"{system_load:.2f}"
        response.headers["X - Rate-Limit"] = str(adjusted_limit)

        return response

    def _calculate_system_load(self, current_time: float) -> float:
        """Calculate simplified system load metric."""
        # Remove old request times (last 5 minutes)
        while self.request_times and self.request_times[0] <= current_time - 300:
            self.request_times.popleft()

        # Calculate requests per second
        if len(self.request_times) < 2:
            return 0.0

        time_span = current_time - self.request_times[0]
        if time_span <= 0:
            return 0.0

        requests_per_second = len(self.request_times) / time_span

        # Calculate error rate
        error_rate = self.error_count / max(self.total_requests, 1)

        # Combine metrics (simplified load calculation)
        load = min(1.0, (requests_per_second / 10.0) + error_rate)

        return load
