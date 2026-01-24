from fastapi import APIRouter

from app.api.admin.actions import router as actions_router
from app.api.admin.analytics import router as analytics_router
from app.api.admin.audit_compliance import router as audit_compliance_router
from app.api.admin.dashboard import router as dashboard_router
from app.api.admin.export import router as export_router
from app.api.admin.logging_dashboard import router as logging_dashboard_router
from app.api.admin.pricing_control import router as pricing_control_router
from app.api.admin.refund_monitoring import router as refund_monitoring_router
from app.api.admin.stats import router as stats_router
from app.api.admin.tier_management import router as tier_management_router
from app.api.admin.user_management import router as user_management_router
from app.api.admin.verification_actions import router as verification_actions_router
from app.api.admin.verification_analytics import router as verification_analytics_router
from app.api.admin.verification_history import router as verification_history_router

router = APIRouter()

router.include_router(dashboard_router, prefix="/api")
router.include_router(verification_analytics_router, prefix="/api")
router.include_router(verification_history_router, prefix="/api")
router.include_router(user_management_router, prefix="/api")
router.include_router(audit_compliance_router, prefix="/api")
router.include_router(analytics_router, prefix="/api")
router.include_router(export_router, prefix="/api")
router.include_router(stats_router, prefix="/api")
router.include_router(tier_management_router, prefix="/api")
router.include_router(actions_router, prefix="/api")
router.include_router(pricing_control_router, prefix="/api")
router.include_router(verification_actions_router, prefix="/api")
router.include_router(logging_dashboard_router, prefix="/api")
router.include_router(refund_monitoring_router, prefix="/api")
