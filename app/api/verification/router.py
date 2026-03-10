"""Verification router - Minimal version for CI fix."""

from fastapi import APIRouter

from app.api.verification.purchase_endpoints import router as purchase_router
from app.api.verification.services_endpoint import router as services_router

# Create main verification router without prefix (main.py adds /api)
router = APIRouter(tags=["Verification"])

# Include purchase routes (main verification functionality)
router.include_router(purchase_router)

# Include services routes
router.include_router(services_router)
