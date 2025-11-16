"""Generic SMS provider interface."""
from abc import ABC, abstractmethod
from typing import Dict, Any

class SMSProviderInterface(ABC):
    """Abstract base class for SMS providers."""
    
    @abstractmethod
    async def get_balance(self) -> Dict[str, Any]:
        """Get account balance."""
        pass
    
    @abstractmethod
    async def buy_number(self, country: str, service: str) -> Dict[str, Any]:
        """Purchase phone number."""
        pass
    
    @abstractmethod
    async def check_sms(self, activation_id: str) -> Dict[str, Any]:
        """Check for SMS messages."""
        pass
    
    @abstractmethod
    async def get_pricing(self, country: str, service: str) -> Dict[str, Any]:
        """Get service pricing."""
        pass

class ProviderManager:
    """Manages multiple SMS providers with failover."""
    
    def __init__(self):
        self.providers = {}
        self.primary_provider = None
    
    def register_provider(self, name: str, provider: SMSProviderInterface, is_primary: bool = False):
        """Register a new provider."""
        self.providers[name] = provider
        if is_primary:
            self.primary_provider = name
    
    def get_provider(self, name: str) -> SMSProviderInterface:
        """Get a specific provider by name."""
        if name not in self.providers:
            raise ValueError(f"Provider '{name}' not found")
        return self.providers[name]
    
    def get_primary_provider(self) -> SMSProviderInterface:
        """Get the primary provider."""
        if not self.primary_provider:
            raise ValueError("No primary provider set")
        return self.providers[self.primary_provider]
    
    async def buy_number_with_failover(self, country: str, service: str) -> Dict[str, Any]:
        """Try to buy number with failover to backup providers."""
        providers_to_try = [self.primary_provider] + [p for p in self.providers.keys() if p != self.primary_provider]
        
        for provider_name in providers_to_try:
            if provider_name in self.providers:
                try:
                    return await self.providers[provider_name].buy_number(country, service)
                except Exception:
                    continue
        
        raise Exception("All providers failed")