"""Verification API routers."""

from . import purchase_endpoints
from .consolidated_verification import router as verify_router
from .purchase_endpoints import router as purchase_router

# Combine routers
router = verify_router
router.include_router(purchase_router)

__all__ = ["router"]
