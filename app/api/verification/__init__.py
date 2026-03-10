"""Verification API routers - Minimal version for CI fix."""

# Import from the main router instead of deleted verification_routes
from .router import router

__all__ = ["router"]
