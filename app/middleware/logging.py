"""Logging middleware - minimal version."""

from starlette.middleware.base import BaseHTTPMiddleware


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Minimal request logging middleware."""
    
    async def dispatch(self, request, call_next):
        return await call_next(request)


class PerformanceMetricsMiddleware(BaseHTTPMiddleware):
    """Minimal performance metrics middleware."""
    
    async def dispatch(self, request, call_next):
        return await call_next(request)


class AuditTrailMiddleware(BaseHTTPMiddleware):
    """Minimal audit trail middleware."""
    
    async def dispatch(self, request, call_next):
        return await call_next(request)
