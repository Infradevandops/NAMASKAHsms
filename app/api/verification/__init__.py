"""Verification API routers."""


# Combine routers
from .consolidated_verification import router as verify_router
from .purchase_endpoints import router as purchase_router

router = verify_router
router.include_router(purchase_router)

__all__ = ["router"]
