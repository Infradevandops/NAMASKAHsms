"""Middleware package for cross-cutting concerns."""

# Security middleware
# Logging middleware
from .logging import (
    AuditTrailMiddleware,
    PerformanceMetricsMiddleware,
    RequestLoggingMiddleware,
)

# Rate limiting middleware
from .rate_limiting import AdaptiveRateLimitMiddleware, RateLimitMiddleware
from .security import (
    AdminRoleMiddleware,
    APIKeyAuthMiddleware,
    CORSMiddleware,
    JWTAuthMiddleware,
    SecurityHeadersMiddleware,
)

__all__ = [
    # Security
    "JWTAuthMiddleware",
    "APIKeyAuthMiddleware",
    "AdminRoleMiddleware",
    "CORSMiddleware",
    "SecurityHeadersMiddleware",
    # Rate Limiting
    "RateLimitMiddleware",
    "AdaptiveRateLimitMiddleware",
    # Logging
    "RequestLoggingMiddleware",
    "PerformanceMetricsMiddleware",
    "AuditTrailMiddleware",
]
