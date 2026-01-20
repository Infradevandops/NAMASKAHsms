from fastapi import APIRouter

from app.api.admin.actions import router as admin_actions_router
from app.api.admin.analytics import router as admin_analytics_router
from app.api.admin.audit_compliance import router as admin_audit_compliance_router

# Admin
from app.api.admin.dashboard import router as admin_dashboard_router
from app.api.admin.export import router as admin_export_router
from app.api.admin.kyc import router as kyc_router
from app.api.admin.logging_dashboard import router as admin_logging_dashboard_router
from app.api.admin.pricing_control import router as admin_pricing_control_router
from app.api.admin.stats import router as admin_stats_router
from app.api.admin.tier_management import router as admin_tier_management_router
from app.api.admin.user_management import router as admin_user_management_router
from app.api.admin.verification_actions import router as admin_verification_actions_router
from app.api.admin.verification_analytics import router as admin_verification_analytics_router
from app.api.admin.verification_history import router as admin_verification_history_router

# Billing
from app.api.billing.router import router as billing_router
from app.api.core.affiliate_endpoints import router as affiliate_router
from app.api.core.analytics_enhanced import router as analytics_enhanced_router
from app.api.core.api_key_endpoints import router as api_key_router

# Core
from app.api.core.auth import router as auth_router
from app.api.core.balance_sync import router as balance_sync_router
from app.api.core.countries import router as countries_router
from app.api.core.dashboard_activity import router as dashboard_activity_router
from app.api.core.gdpr import router as gdpr_router
from app.api.core.notification_endpoints import router as notification_router
from app.api.core.preferences import router as preferences_router
from app.api.core.services import router as services_router
from app.api.core.system import router as system_router
from app.api.core.textverified_balance import router as textverified_balance_router
from app.api.core.user_profile import router as user_profile_router
from app.api.core.user_settings import router as user_settings_router
from app.api.core.user_settings_endpoints import router as user_settings_endpoints_router
from app.api.core.wallet import router as wallet_router
from app.api.verification.bulk_purchase_endpoints import router as bulk_purchase_router
from app.api.verification.carrier_endpoints import router as carrier_router

# Verification Leaves
from app.api.verification.consolidated_verification import router as verify_router
from app.api.verification.pricing import router as pricing_router
from app.api.verification.purchase_endpoints import router as purchase_router
from app.api.verification.status_polling import router as status_polling_router
from app.api.verification.textverified_endpoints import router as textverified_router

v1_router = APIRouter(prefix="/api/v1")

# Include Core Routers
v1_router.include_router(auth_router)
v1_router.include_router(gdpr_router)
v1_router.include_router(notification_router)
v1_router.include_router(dashboard_activity_router)
v1_router.include_router(textverified_balance_router)
v1_router.include_router(user_profile_router)
v1_router.include_router(countries_router)
v1_router.include_router(services_router)
v1_router.include_router(system_router)
v1_router.include_router(api_key_router)
v1_router.include_router(user_settings_router)
v1_router.include_router(user_settings_endpoints_router)
v1_router.include_router(preferences_router)
v1_router.include_router(affiliate_router)
v1_router.include_router(analytics_enhanced_router)
v1_router.include_router(balance_sync_router)
v1_router.include_router(wallet_router)

# Include Admin Routers
v1_router.include_router(admin_dashboard_router)
v1_router.include_router(admin_verification_analytics_router)
v1_router.include_router(admin_verification_history_router)
v1_router.include_router(admin_user_management_router)
v1_router.include_router(admin_audit_compliance_router)
v1_router.include_router(admin_analytics_router)
v1_router.include_router(admin_export_router)
v1_router.include_router(admin_stats_router)
v1_router.include_router(admin_tier_management_router)
v1_router.include_router(admin_actions_router)
v1_router.include_router(admin_pricing_control_router)
v1_router.include_router(admin_verification_actions_router)
v1_router.include_router(admin_logging_dashboard_router)
v1_router.include_router(kyc_router)

# Include Billing
# Assuming billing_router is an aggregator, we might face similar issues.
# For now, keep it, but note potential double-prefix.
v1_router.include_router(billing_router)

# Include Verification Leaves
v1_router.include_router(verify_router)
v1_router.include_router(textverified_router)
v1_router.include_router(pricing_router)
v1_router.include_router(carrier_router)
v1_router.include_router(purchase_router)
v1_router.include_router(bulk_purchase_router)
v1_router.include_router(status_polling_router)
