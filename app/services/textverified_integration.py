"""High-level TextVerified integration service."""
from typing import Dict, Any, Optional, List
from app.core.logging import get_logger
from app.services.textverified_api import get_textverified_client
from app.core.unified_cache import cache

logger = get_logger(__name__)


class TextVerifiedIntegration:
    """High-level integration with TextVerified API."""

    def __init__(self):
        self.client = get_textverified_client()
        self.cache = cache

    async def get_account_balance(self, force_refresh: bool = False) -> float:
        """Get real account balance from TextVerified."""
        cache_key = "textverified:balance"

        if not force_refresh:
            cached = await self.cache.get(cache_key)
            if cached is not None:
                return float(cached)

        try:
            data = await self.client.get_account_balance()
            balance = data.get("balance", 0.0)
            await self.cache.set(cache_key, str(balance), ttl=300)
            return balance
        except Exception as e:
            logger.error(f"Failed to get balance: {e}")
            raise

    async def create_verification(
        self,
        service: str,
        area_code: Optional[str] = None,
        carrier: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Create real SMS verification."""
        try:
            result = await self.client.create_verification(
                service=service, area_code=area_code, carrier=carrier
            )
            logger.info(f"Verification created: {result['id']}")
            return result
        except Exception as e:
            logger.error(f"Failed to create verification: {e}")
            raise

    async def get_verification_status(self, verification_id: str) -> Dict[str, Any]:
        """Get verification status."""
        try:
            return await self.client.get_verification_status(verification_id)
        except Exception as e:
            logger.error(f"Failed to get verification status: {e}")
            raise

    async def get_sms_codes(self, reservation_id: str) -> List[str]:
        """Get SMS codes from messages."""
        try:
            messages = await self.client.get_sms_messages(reservation_id)
            codes = []
            for msg in messages:
                text = msg.get("text", "")
                import re
                numbers = re.findall(r"\d{4,6}", text)
                codes.extend(numbers)
            return codes
        except Exception as e:
            logger.error(f"Failed to get SMS codes: {e}")
            return []

    async def create_rental(
        self,
        service: str,
        duration_days: int,
        renewable: bool = False,
    ) -> Dict[str, Any]:
        """Create real phone number rental."""
        try:
            result = await self.client.create_rental(
                service=service, duration_days=duration_days, renewable=renewable
            )
            logger.info(f"Rental created: {result['id']}")
            return result
        except Exception as e:
            logger.error(f"Failed to create rental: {e}")
            raise

    async def get_active_rentals(self) -> List[Dict[str, Any]]:
        """Get all active rentals."""
        try:
            renewable = await self.client.get_rentals("renewable")
            non_renewable = await self.client.get_rentals("nonrenewable")
            return renewable + non_renewable
        except Exception as e:
            logger.error(f"Failed to get rentals: {e}")
            return []

    async def extend_rental(self, rental_id: str, duration_days: int) -> Dict[str, Any]:
        """Extend rental duration."""
        try:
            result = await self.client.extend_rental(rental_id, duration_days)
            logger.info(f"Rental extended: {rental_id}")
            return result
        except Exception as e:
            logger.error(f"Failed to extend rental: {e}")
            raise

    async def get_services_list(self, force_refresh: bool = False) -> List[Dict[str, Any]]:
        """Get available services with caching."""
        cache_key = "textverified:services"

        if not force_refresh:
            cached = await self.cache.get(cache_key)
            if cached:
                import json
                return json.loads(cached)

        try:
            services = await self.client.get_services()
            import json
            await self.cache.set(cache_key, json.dumps(services), ttl=3600)
            return services
        except Exception as e:
            logger.error(f"Failed to get services: {e}")
            return []

    async def get_area_codes_list(self, force_refresh: bool = False) -> List[Dict[str, Any]]:
        """Get available area codes with caching."""
        cache_key = "textverified:area_codes"

        if not force_refresh:
            cached = await self.cache.get(cache_key)
            if cached:
                import json
                return json.loads(cached)

        try:
            codes = await self.client.get_area_codes()
            import json
            await self.cache.set(cache_key, json.dumps(codes), ttl=3600)
            return codes
        except Exception as e:
            logger.error(f"Failed to get area codes: {e}")
            return []

    async def get_service_pricing(self, service: str) -> float:
        """Get service pricing."""
        try:
            data = await self.client.get_pricing(service, "verification")
            return data.get("cost", 0.0)
        except Exception as e:
            logger.error(f"Failed to get pricing: {e}")
            return 0.0


# Global instance
_integration: Optional[TextVerifiedIntegration] = None


def get_textverified_integration() -> TextVerifiedIntegration:
    """Get or create TextVerified integration instance."""
    global _integration
    if _integration is None:
        _integration = TextVerifiedIntegration()
    return _integration
