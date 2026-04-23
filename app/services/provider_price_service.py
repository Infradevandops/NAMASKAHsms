"""Provider price service for live price tracking and markup calculation."""

import asyncio
from typing import Any, Dict, List, Optional
from decimal import Decimal

from app.core.logging import get_logger
from app.services.textverified_service import TextVerifiedService
from app.services.pricing_template_service import PricingTemplateService
from app.core.unified_cache import cache

logger = get_logger(__name__)

_LIVE_PRICES_CACHE_KEY = "admin:live_provider_prices"
_LIVE_PRICES_TTL = 300  # 5 minutes


class ProviderPriceService:
    """Service for fetching and processing live provider prices for admin dashboard."""

    def __init__(self, db_session=None):
        self.tv_service = TextVerifiedService()
        self.db = db_session
        self.pricing_template_service = PricingTemplateService(db_session) if db_session else None

    async def get_live_prices(self, force_refresh: bool = False) -> Dict[str, Any]:
        """
        Fetch live prices from provider and apply current platform markup.
        Results are cached for 5 minutes.
        """
        if not force_refresh:
            try:
                cached = await cache.get(_LIVE_PRICES_CACHE_KEY)
                if cached:
                    return cached
            except Exception as e:
                logger.warning(f"Failed to read live prices cache: {e}")

        try:
            # 1. Fetch live costs from TextVerified
            services = await self.tv_service.get_services_list()
            
            # 2. Get active pricing template for markup
            active_template = None
            if self.pricing_template_service:
                active_template = self.pricing_template_service.get_active_template()
            
            markup = Decimal("1.1000")
            if active_template and hasattr(active_template, 'markup_multiplier'):
                markup = active_template.markup_multiplier
            
            # 3. Process and format
            processed_prices = []
            for svc in services:
                cost = svc.get("cost")
                if cost is not None:
                    provider_cost = Decimal(str(cost))
                    platform_price = (provider_cost * markup).quantize(Decimal("0.01"))
                    
                    processed_prices.append({
                        "service_id": svc["id"],
                        "service_name": svc["name"],
                        "provider_cost": float(provider_cost),
                        "platform_price": float(platform_price),
                        "markup_multiplier": float(markup),
                        "markup_percentage": float((markup - 1) * 100),
                        "currency": "USD"
                    })

            result = {
                "prices": processed_prices,
                "count": len(processed_prices),
                "template_name": active_template.name if active_template else "Default",
                "updated_at": asyncio.get_event_loop().time() # Placeholder, we'll use actual timestamp in final
            }

            # 4. Cache result
            try:
                await cache.set(_LIVE_PRICES_CACHE_KEY, result, _LIVE_PRICES_TTL)
            except Exception as e:
                logger.warning(f"Failed to cache live prices: {e}")

            return result

        except Exception as e:
            logger.error(f"Failed to fetch live provider prices: {e}")
            raise RuntimeError(f"Could not fetch live prices: {str(e)}")

    def get_popular_services(self, prices: List[Dict[str, Any]], limit: int = 20) -> List[Dict[str, Any]]:
        """Filter and return popular services."""
        popular_ids = {
            "whatsapp", "telegram", "instagram", "facebook", 
            "twitter", "google", "microsoft", "amazon", 
            "netflix", "uber", "tiktok", "snapchat", "tinder",
            "discord", "linkedin", "paypal", "airbnb", "spotify"
        }
        
        filtered = [p for p in prices if p["service_id"].lower() in popular_ids]
        # Sort by service name or price if needed
        return sorted(filtered, key=lambda x: x["service_name"])[:limit]
