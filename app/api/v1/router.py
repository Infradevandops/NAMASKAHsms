"""API v1 router."""

from fastapi import APIRouter

from app.api.activities import router as activities_router
from app.api.admin.actions import router as admin_actions_router
from app.api.admin.analytics import router as admin_analytics_router
from app.api.admin.audit_compliance import router as admin_audit_compliance_router
from app.api.admin.dashboard import router as admin_dashboard_router
from app.api.admin.export import router as admin_export_router
from app.api.admin.logging_dashboard import router as admin_logging_dashboard_router
from app.api.admin.pricing_control import router as admin_pricing_control_router
from app.api.admin.stats import router as admin_stats_router
from app.api.admin.tier_management import router as admin_tier_management_router
from app.api.admin.user_management import router as admin_user_management_router
from app.api.admin.verification_actions import (
    router as admin_verification_actions_router,
)
from app.api.admin.verification_analytics import (
    router as admin_verification_analytics_router,
)
from app.api.admin.verification_history import (
    router as admin_verification_history_router,
)
from app.api.auth_routes import router as auth_router
from app.api.billing.router import router as billing_router
from app.api.core.notification_endpoints import router as notification_router
from app.api.core.router import router as core_router
from app.api.verification.router import router as verification_router

# Create v1 router
v1_router = APIRouter(prefix="/api/v1", tags=["API v1"])

# Core user-facing routes
v1_router.include_router(core_router)
v1_router.include_router(auth_router)
v1_router.include_router(notification_router)

# Activities
v1_router.include_router(activities_router)

# Admin routers
v1_router.include_router(admin_actions_router)
v1_router.include_router(admin_analytics_router)
v1_router.include_router(admin_audit_compliance_router)
v1_router.include_router(admin_dashboard_router)
v1_router.include_router(admin_export_router)
v1_router.include_router(admin_logging_dashboard_router)
v1_router.include_router(admin_pricing_control_router)
v1_router.include_router(admin_stats_router)
v1_router.include_router(admin_tier_management_router)
v1_router.include_router(admin_user_management_router)
v1_router.include_router(admin_verification_actions_router)
v1_router.include_router(admin_verification_analytics_router)
v1_router.include_router(admin_verification_history_router)

# Billing and Verification
v1_router.include_router(billing_router)
v1_router.include_router(verification_router)
