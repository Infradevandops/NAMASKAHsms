from fastapi import APIRouter
from app.api.verification.textverified_endpoints import router as textverified_router
from app.api.verification.pricing import router as pricing_router
from app.api.verification.carrier_endpoints import router as carrier_router
from app.api.verification.consolidated_verification import router as verify_router
from app.api.verification.purchase_endpoints import router as purchase_router
from app.api.verification.bulk_purchase_endpoints import router as bulk_purchase_router
from app.api.verification.status_polling import router as status_polling_router

router = APIRouter()

router.include_router(verify_router)
router.include_router(textverified_router)
router.include_router(pricing_router)
router.include_router(carrier_router)
router.include_router(purchase_router)
router.include_router(bulk_purchase_router)
router.include_router(status_polling_router)
