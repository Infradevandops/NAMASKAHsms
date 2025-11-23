"""Rate limiting middleware."""
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from app.core.rate_limiter import rate_limiter

logger = get_logger(__name__)


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Middleware for rate limiting."""

    async def dispatch(self, request: Request, call_next):
        # Get user ID and IP
        user_id = getattr(request.state, "user_id", "anonymous")
        ip = request.client.host if request.client else "unknown"

        # Check rate limit
        allowed, retry_after = rate_limiter.check_limit(user_id, ip)

        if not allowed:
            logger.warning(f"Rate limit exceeded for {user_id} from {ip}")
            return JSONResponse(
                status_code=429,
                content={"error": "Too many requests"},
                headers={"Retry - After": str(retry_after)}
            )

        response = await call_next(request)
        response.headers["X - RateLimit-Limit"] = str(rate_limiter.user_limit)
        response.headers["X - RateLimit-Remaining"] = str(
            int(rate_limiter.user_buckets.get(user_id).tokens)
        )

        return response
