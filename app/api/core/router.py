

from fastapi import APIRouter
from app.api.core.affiliate_endpoints import router as affiliate_router
from app.api.core.analytics_enhanced import router as analytics_enhanced_router
from app.api.core.api_key_endpoints import router as api_key_router
from app.api.core.auth import router as auth_router
from app.api.core.balance_sync import router as balance_sync_router
from app.api.core.blacklist import router as blacklist_router
from app.api.core.countries import router as countries_router
from app.api.core.dashboard_activity import router as dashboard_activity_router
from app.api.core.forwarding import router as forwarding_router
from app.api.core.gdpr import router as gdpr_router
from app.api.core.notification_endpoints import router as notification_router
from app.api.core.preferences import router as preferences_router
from app.api.core.referrals import router as referrals_router
from app.api.core.services import router as services_router
from app.api.core.system import router as system_router
from app.api.core.textverified_balance import router as textverified_balance_router
from app.api.core.user_profile import router as user_profile_router
from app.api.core.user_settings import router as user_settings_router
from app.api.core.user_settings_endpoints import router as user_settings_endpoints_router
from app.api.core.wallet import router as wallet_router
from app.api.core.webhooks import router as webhooks_router

router = APIRouter()

router.include_router(auth_router, prefix="/api")
router.include_router(gdpr_router, prefix="/api")
router.include_router(notification_router)
router.include_router(dashboard_activity_router)
router.include_router(textverified_balance_router)
router.include_router(user_profile_router, prefix="/api")
router.include_router(countries_router, prefix="/api")
router.include_router(services_router)
router.include_router(system_router)
router.include_router(api_key_router)
router.include_router(user_settings_router, prefix="/api")
router.include_router(user_settings_endpoints_router)
router.include_router(preferences_router)
router.include_router(affiliate_router)
router.include_router(analytics_enhanced_router)
router.include_router(balance_sync_router)
router.include_router(wallet_router)
router.include_router(blacklist_router)
router.include_router(forwarding_router, prefix="/api")
router.include_router(webhooks_router, prefix="/api")
router.include_router(referrals_router, prefix="/api")