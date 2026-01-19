from fastapi import APIRouter

from app.api.billing.credit_endpoints import router as credit_router
from app.api.billing.payment_endpoints import router as payment_router
from app.api.billing.payment_history_endpoints import router as payment_history_router
from app.api.billing.pricing_endpoints import router as pricing_endpoints_router
from app.api.billing.refund_endpoints import router as refund_router
from app.api.billing.tier_endpoints import router as tier_router

router = APIRouter()

router.include_router(credit_router)
router.include_router(payment_router)
router.include_router(payment_history_router)
router.include_router(pricing_endpoints_router)
router.include_router(refund_router)
router.include_router(tier_router)
