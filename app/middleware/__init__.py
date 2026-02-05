"""Middleware package for cross-cutting concerns."""

# Logging middleware
from .logging import (
    AuditTrailMiddleware,
    PerformanceMetricsMiddleware,
    RequestLoggingMiddleware,
)

# Rate limiting middleware
from .rate_limiting import rate_limit

# Security middleware
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
    "rate_limit",
    # Logging
    "RequestLoggingMiddleware",
    "PerformanceMetricsMiddleware",
    "AuditTrailMiddleware",
]
