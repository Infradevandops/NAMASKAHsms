"""Verification router - Minimal version for CI fix."""

from fastapi import APIRouter

from app.api.verification.area_code_endpoints import router as area_code_router
from app.api.verification.cancel_endpoint import router as cancel_router
from app.api.verification.outcome_endpoint import router as outcome_router
from app.api.verification.purchase_endpoints import router as purchase_router
from app.api.verification.rental_endpoints import router as rental_router
from app.api.verification.services_endpoint import router as services_router
from app.api.verification.status_polling import router as status_router

# Create main verification router without prefix (main.py adds /api)
router = APIRouter(tags=["Verification"])

# Include purchase routes (main verification functionality)
router.include_router(purchase_router)

# Include services routes
router.include_router(services_router)

# Include rental routes
router.include_router(rental_router)

# Include status polling routes

router.include_router(status_router)

# Include cancel routes
router.include_router(cancel_router, prefix="/verification")

# Include outcome routes
router.include_router(outcome_router)

# Include area code routes
router.include_router(area_code_router)
