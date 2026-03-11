from fastapi import APIRouter

from app.api.billing.credit_endpoints import router as credit_router
from app.api.billing.invoice_endpoints import router as invoice_router
from app.api.billing.payment_endpoints import router as payment_router
from app.api.billing.payment_history_endpoints import router as payment_history_router
from app.api.billing.payment_method_endpoints import router as payment_method_router
from app.api.billing.pricing_endpoints import router as pricing_endpoints_router
from app.api.billing.refund_endpoints import router as refund_router
from app.api.billing.tier_endpoints import router as tier_router

router = APIRouter()

router.include_router(credit_router, prefix="/wallet", tags=["wallet"])
router.include_router(payment_router, prefix="/wallet/paystack", tags=["payment"])
router.include_router(payment_history_router, prefix="/wallet", tags=["wallet"])
router.include_router(pricing_endpoints_router, prefix="/billing", tags=["billing"])
router.include_router(refund_router, prefix="/wallet/refund", tags=["refund"])
router.include_router(tier_router, prefix="/billing/tiers", tags=["tiers"])
router.include_router(
    payment_method_router, prefix="/billing/payment-method", tags=["payment-method"]
)
router.include_router(invoice_router, prefix="/wallet/invoice", tags=["invoice"])
