"""SMS provider factory with multi - provider support."""
from app.services.textverified_service_updated import TextVerifiedService
from app.services.sms_provider_interface import ProviderManager
from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


def create_provider_manager() -> ProviderManager:
    """Create provider manager with all available providers."""
    manager = ProviderManager()

    # Register providers in priority order
    # TextVerified is the primary SMS provider
    if settings.textverified_api_key:
        manager.register_provider("textverified",
                                  TextVerifiedService(), is_primary=True)
    else:
        logger.warning("TEXTVERIFIED_API_KEY not configured; no SMS providers available")

    # Other providers temporarily disabled until they implement the interface
    # manager.register_provider("sms_activate", SMSActivateService())
    # manager.register_provider("getsms", GetSMSService())

    return manager


# Global provider manager instance
provider_manager = create_provider_manager()
