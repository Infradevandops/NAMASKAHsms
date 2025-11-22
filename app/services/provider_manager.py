"""Multi - provider SMS service manager."""
from typing import Dict, List, Any
from enum import Enum
from app.core.logging import get_logger

logger = get_logger(__name__)


class ProviderType(str, Enum):
    TEXTVERIFIED = "textverified"
    FIVESIM = "5sim"
    GETSMS = "getsms"
    SMS_ACTIVATE = "sms - activate"


class ProviderManager:
    """Manages multiple SMS providers with fallback logic."""

    def __init__(self):
        self.primary_provider = ProviderType.TEXTVERIFIED
        self.fallback_providers = [
            ProviderType.FIVESIM,
            ProviderType.GETSMS,
            ProviderType.SMS_ACTIVATE
        ]
        self.providers = {}
        self._init_providers()

    def _init_providers(self):
        """Initialize all available providers."""
        from app.services.textverified_service_updated import TextVerifiedService

        self.providers[ProviderType.TEXTVERIFIED] = TextVerifiedService()

        # Placeholder for other providers
        self.providers[ProviderType.FIVESIM] = None
        self.providers[ProviderType.GETSMS] = None
        self.providers[ProviderType.SMS_ACTIVATE] = None

    async def get_countries(self) -> List[Dict[str, Any]]:
        """Get countries from primary provider."""
        provider = self.providers[self.primary_provider]
        if provider and provider.enabled:
            try:
                return await provider.get_countries()
            except Exception as e:
                logger.error(f"Primary provider error: {e}")
                return await self._fallback_get_countries()
        return await self._fallback_get_countries()

    async def _fallback_get_countries(self) -> List[Dict[str, Any]]:
        """Fallback to other providers for countries."""
        for provider_type in self.fallback_providers:
            provider = self.providers[provider_type]
            if provider and provider.enabled:
                try:
                    return await provider.get_countries()
                except Exception as e:
                    logger.warning(f"Fallback provider {provider_type} error: {e}")
        return []

    async def get_services(self, country: str) -> List[Dict[str, Any]]:
        """Get services from primary provider."""
        provider = self.providers[self.primary_provider]
        if provider and provider.enabled:
            try:
                return await provider.get_services(country)
            except Exception as e:
                logger.error(f"Primary provider error: {e}")
                return await self._fallback_get_services(country)
        return await self._fallback_get_services(country)

    async def _fallback_get_services(self, country: str) -> List[Dict[str, Any]]:
        """Fallback to other providers for services."""
        for provider_type in self.fallback_providers:
            provider = self.providers[provider_type]
            if provider and provider.enabled:
                try:
                    return await provider.get_services(country)
                except Exception as e:
                    logger.warning(f"Fallback provider {provider_type} error: {e}")
        return []

    async def buy_number(self, country: str, service: str) -> Dict[str, Any]:
        """Buy number from primary provider."""
        provider = self.providers[self.primary_provider]
        if provider and provider.enabled:
            try:
                return await provider.buy_number(country, service)
            except Exception as e:
                logger.error(f"Primary provider error: {e}")
                return await self._fallback_buy_number(country, service)
        return await self._fallback_buy_number(country, service)

    async def _fallback_buy_number(self, country: str, service: str) -> Dict[str, Any]:
        """Fallback to other providers for buying number."""
        for provider_type in self.fallback_providers:
            provider = self.providers[provider_type]
            if provider and provider.enabled:
                try:
                    return await provider.buy_number(country, service)
                except Exception as e:
                    logger.warning(f"Fallback provider {provider_type} error: {e}")
        raise Exception("All providers failed")

    async def check_sms(self, activation_id: str,
                        provider: str = None) -> Dict[str, Any]:
        """Check SMS from specific or primary provider."""
        if provider:
            p = self.providers.get(provider)
            if p and p.enabled:
                return await p.check_sms(activation_id)

        provider_obj = self.providers[self.primary_provider]
        if provider_obj and provider_obj.enabled:
            return await provider_obj.check_sms(activation_id)

        return {"status": "error", "message": "No provider available"}

    def get_provider_status(self) -> Dict[str, bool]:
        """Get status of all providers."""
        return {
            name: provider.enabled if provider else False
            for name, provider in self.providers.items()
        }


provider_manager = ProviderManager()
