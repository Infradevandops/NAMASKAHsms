"""SMS provider factory with multi-provider support."""
from app.services.fivesim_service import FiveSimService
from app.services.sms_activate_service import SMSActivateService
from app.services.getsms_service import GetSMSService
from app.services.textverified_service import TextVerifiedService
from app.services.sms_provider_interface import ProviderManager

def create_provider_manager() -> ProviderManager:
    """Create provider manager with all available providers."""
    manager = ProviderManager()
    
    # Register providers in priority order
    manager.register_provider("5sim", FiveSimService(), is_primary=True)
    manager.register_provider("sms_activate", SMSActivateService())
    manager.register_provider("getsms", GetSMSService())
    manager.register_provider("textverified", TextVerifiedService())
    
    return manager

# Global provider manager instance
provider_manager = create_provider_manager()