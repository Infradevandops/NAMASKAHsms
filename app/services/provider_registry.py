"""Provider registry for initializing and managing all SMS providers."""
from app.services.provider_system import ProviderManager

logger = get_logger(__name__)


def initialize_providers() -> ProviderManager:
    """Initialize all available SMS providers."""
    manager = ProviderManager()

    # Initialize TextVerified provider
    try:
        textverified = TextVerifiedProvider()
        if textverified.enabled:
            manager.register_provider(textverified, is_primary=True, priority=100)
            logger.info("TextVerified provider registered as primary")
        else:
            logger.warning("TextVerified provider not enabled")
    except Exception as e:
        logger.error(f"Failed to initialize TextVerified provider: {e}")

    # Future providers can be added here:
    # try:
    #     fivesim = FiveSimProvider()
    #     if fivesim.enabled:
    #         manager.register_provider(fivesim, priority = 90)
    # except Exception as e:
    #     logger.error(f"Failed to initialize 5SIM provider: {e}")

    # try:
    #     smsactivate = SMSActivateProvider()
    #     if smsactivate.enabled:
    #         manager.register_provider(smsactivate, priority = 80)
    # except Exception as e:
    #     logger.error(f"Failed to initialize SMS - Activate provider: {e}")

    available_providers = manager.get_available_providers()
    if available_providers:
        logger.info(f"Initialized {len(available_providers)} SMS providers: {available_providers}")
    else:
        logger.error("No SMS providers available!")

    return manager


# Global provider manager instance
provider_manager = initialize_providers()
