"""
Rate Limiting Middleware
Prevent API abuse with endpoint-specific rate limits
"""

from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
import logging

logger = logging.getLogger(__name__)

# Initialize limiter
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["100/minute"],
    storage_uri="memory://",  # Use Redis in production
    strategy="fixed-window"
)

# Rate limit configurations by endpoint type
RATE_LIMITS = {
    # Auth endpoints (strict)
    "auth_login": "5/minute",
    "auth_register": "3/hour",
    "auth_password_reset": "3/hour",
    
    # Payment endpoints (moderate)
    "payment_initialize": "10/minute",
    "payment_verify": "20/minute",
    
    # Verification endpoints (moderate)
    "verification_create": "20/minute",
    "verification_status": "60/minute",
    
    # Wallet endpoints (lenient)
    "wallet_balance": "60/minute",
    "wallet_transactions": "30/minute",
    
    # API endpoints (strict for external)
    "api_external": "100/hour",
}


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Custom rate limiting middleware with logging"""
    
    async def dispatch(self, request: Request, call_next):
        try:
            response = await call_next(request)
            return response
        except RateLimitExceeded as e:
            # Log rate limit violation
            logger.warning(
                f"Rate limit exceeded: {get_remote_address(request)} "
                f"on {request.url.path}"
            )
            
            # Return 429 with retry-after header
            return Response(
                content='{"detail":"Rate limit exceeded. Please try again later."}',
                status_code=429,
                headers={
                    "Retry-After": str(e.detail.split("Retry after ")[1] if "Retry after" in e.detail else "60"),
                    "Content-Type": "application/json"
                }
            )


def get_limiter():
    """Get limiter instance"""
    return limiter


def rate_limit_handler(request: Request, exc: RateLimitExceeded):
    """Custom rate limit error handler"""
    logger.warning(
        f"Rate limit: {get_remote_address(request)} "
        f"on {request.url.path}"
    )
    return Response(
        content='{"detail":"Too many requests. Please slow down."}',
        status_code=429,
        headers={"Content-Type": "application/json"}
    )
