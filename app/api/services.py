"""Services API router for TextVerified integration."""
from fastapi import APIRouter, HTTPException
from app.services.textverified_service import TextVerifiedService
from typing import Dict, Any

router = APIRouter(prefix="/verify", tags=["Services"])

@router.get("/services")
async def get_available_services():
    """Get available services from TextVerified."""
    try:
        textverified = TextVerifiedService()
        result = await textverified.get_services()
        
        if "error" in result:
            return get_fallback_services()
        
        services = result.get("services", [])
        formatted_services = []
        
        for service in services:
            if isinstance(service, dict):
                formatted_services.append({
                    "id": service.get("id"),
                    "name": service.get("name", "").lower(),
                    "display_name": service.get("name", ""),
                    "price": service.get("price", 0.50),
                    "available": True
                })
        
        return {"services": formatted_services}
    except Exception:
        return get_fallback_services()

@router.get("/services/list")
async def get_services_list():
    """Get services list in categorized format for frontend."""
    try:
        textverified = TextVerifiedService()
        result = await textverified.get_services()
        
        if "error" not in result and result.get("services"):
            services = result.get("services", [])
            return format_services_categorized(services)
        else:
            return get_fallback_services_categorized()
    except Exception:
        return get_fallback_services_categorized()

@router.get("/services/price/{service_name}")
async def get_service_price(service_name: str):
    """Get price for a specific service."""
    try:
        fallback_prices = {
            'whatsapp': 0.75, 'telegram': 0.75, 'discord': 0.75, 'google': 0.75,
            'instagram': 1.00, 'facebook': 1.00, 'twitter': 1.00, 'tiktok': 1.00,
            'paypal': 1.50, 'venmo': 1.50, 'cashapp': 1.50
        }
        
        base_price = fallback_prices.get(service_name.lower(), 2.00)
        voice_premium = 0.30
        
        return {
            "service_name": service_name,
            "base_price": base_price,
            "voice_premium": voice_premium,
            "total_sms": base_price,
            "total_voice": base_price + voice_premium
        }
    except Exception:
        return {
            "service_name": service_name,
            "base_price": 2.00,
            "voice_premium": 0.30,
            "total_sms": 2.00,
            "total_voice": 2.30
        }

@staticmethod
def get_fallback_services() -> Dict[str, Any]:
    """Return fallback services when API fails."""
    fallback_services = [
        {"id": "telegram", "name": "telegram", "display_name": "Telegram", "price": 0.75, "available": True},
        {"id": "whatsapp", "name": "whatsapp", "display_name": "WhatsApp", "price": 0.75, "available": True},
        {"id": "discord", "name": "discord", "display_name": "Discord", "price": 0.75, "available": True},
        {"id": "google", "name": "google", "display_name": "Google", "price": 0.75, "available": True},
        {"id": "instagram", "name": "instagram", "display_name": "Instagram", "price": 1.00, "available": True},
        {"id": "facebook", "name": "facebook", "display_name": "Facebook", "price": 1.00, "available": True},
        {"id": "twitter", "name": "twitter", "display_name": "Twitter", "price": 1.00, "available": True},
        {"id": "tiktok", "name": "tiktok", "display_name": "TikTok", "price": 1.00, "available": True}
    ]
    return {"services": fallback_services}

@staticmethod
def get_fallback_services_categorized() -> Dict[str, Any]:
    """Return categorized fallback services."""
    return {
        "categories": {
            "Social": ["telegram", "whatsapp", "discord", "instagram", "facebook", "twitter", "tiktok", "snapchat"],
            "Finance": ["paypal", "cashapp", "venmo", "coinbase", "robinhood"],
            "Shopping": ["amazon", "ebay", "etsy", "mercari"],
            "Gaming": ["steam", "epic", "xbox", "playstation"],
            "Other": ["google", "microsoft", "apple", "uber", "lyft"]
        },
        "tiers": {
            "tier1": {"name": "High-Demand", "price": 0.75, "services": ["whatsapp", "telegram", "discord", "google"]},
            "tier2": {"name": "Standard", "price": 1.0, "services": ["instagram", "facebook", "twitter", "tiktok"]},
            "tier3": {"name": "Premium", "price": 1.5, "services": ["paypal"]},
            "tier4": {"name": "Specialty", "price": 2.0, "services": []}
        },
        "uncategorized": []
    }

@staticmethod
def format_services_categorized(services) -> Dict[str, Any]:
    """Format TextVerified services into categorized structure."""
    categories = {
        "Social": [],
        "Finance": [],
        "Shopping": [],
        "Gaming": [],
        "Other": []
    }
    
    social_keywords = ['telegram', 'whatsapp', 'discord', 'instagram', 'facebook', 'twitter', 'tiktok', 'snapchat']
    finance_keywords = ['paypal', 'cashapp', 'venmo', 'coinbase', 'robinhood']
    shopping_keywords = ['amazon', 'ebay', 'etsy', 'mercari']
    gaming_keywords = ['steam', 'epic', 'xbox', 'playstation']
    
    for service in services:
        service_name = service.get('name', '').lower()
        if any(keyword in service_name for keyword in social_keywords):
            categories["Social"].append(service_name)
        elif any(keyword in service_name for keyword in finance_keywords):
            categories["Finance"].append(service_name)
        elif any(keyword in service_name for keyword in shopping_keywords):
            categories["Shopping"].append(service_name)
        elif any(keyword in service_name for keyword in gaming_keywords):
            categories["Gaming"].append(service_name)
        else:
            categories["Other"].append(service_name)
    
    return {
        "categories": categories,
        "tiers": {
            "tier1": {"name": "High-Demand", "price": 0.75, "services": categories["Social"][:4]},
            "tier2": {"name": "Standard", "price": 1.0, "services": categories["Social"][4:] + categories["Other"][:2]},
            "tier3": {"name": "Premium", "price": 1.5, "services": categories["Finance"][:2]},
            "tier4": {"name": "Specialty", "price": 2.0, "services": categories["Gaming"] + categories["Shopping"]}
        },
        "uncategorized": []
    }