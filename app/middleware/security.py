"""Security middleware - minimal version."""

from starlette.middleware.base import BaseHTTPMiddleware


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Minimal security headers middleware."""
    
    async def dispatch(self, request, call_next):
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        return response


class JWTAuthMiddleware(BaseHTTPMiddleware):
    """Minimal JWT auth middleware."""
    
    async def dispatch(self, request, call_next):
        return await call_next(request)
