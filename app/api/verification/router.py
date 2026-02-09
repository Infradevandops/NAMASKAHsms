"""Verification router - Minimal version for CI fix."""

from fastapi import APIRouter
from app.api.verification.verification_routes import router as verify_router
from app.api.verification.services_endpoint import router as services_router

# Create main verification router without prefix (main.py adds /api)
router = APIRouter(tags=["Verification"])

# Include verification routes with /verify prefix
router.include_router(verify_router)

# Include services routes
router.include_router(services_router)

# Note: Other verification routers temporarily disabled for CI fix
# They can be re-enabled once syntax errors are fixed
