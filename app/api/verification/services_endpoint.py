"""Services endpoint for verification system."""


from fastapi import APIRouter, Query
from typing import Optional

router = APIRouter(prefix="/api/countries", tags=["Services"])


@router.get("/{country}/services")
async def get_services(
    country: str,
    areaCode: Optional[str] = Query(None, description="Area code filter")
):
    """Get available services for a country and optional area code.

    Currently supports US services only.
    """
if country.upper() != "USA" and country.upper() != "US":
        return {"services": [], "total": 0, "message": "Only US services supported"}

    # Popular services that work with SMS verification
    services = [
        {
            "name": "whatsapp",
            "display_name": "WhatsApp",
            "category": "messaging",
            "popularity": 95,
            "base_price": 0.15,
            "description": "Popular messaging app"
        },
        {
            "name": "telegram",
            "display_name": "Telegram",
            "category": "messaging",
            "popularity": 85,
            "base_price": 0.12,
            "description": "Secure messaging platform"
        },
        {
            "name": "discord",
            "display_name": "Discord",
            "category": "gaming",
            "popularity": 80,
            "base_price": 0.18,
            "description": "Gaming and community platform"
        },
        {
            "name": "instagram",
            "display_name": "Instagram",
            "category": "social",
            "popularity": 90,
            "base_price": 0.20,
            "description": "Photo and video sharing"
        },
        {
            "name": "facebook",
            "display_name": "Facebook",
            "category": "social",
            "popularity": 85,
            "base_price": 0.22,
            "description": "Social networking platform"
        },
        {
            "name": "twitter",
            "display_name": "Twitter/X",
            "category": "social",
            "popularity": 75,
            "base_price": 0.25,
            "description": "Social media and news"
        },
        {
            "name": "google",
            "display_name": "Google",
            "category": "tech",
            "popularity": 95,
            "base_price": 0.10,
            "description": "Google services"
        },
        {
            "name": "microsoft",
            "display_name": "Microsoft",
            "category": "tech",
            "popularity": 80,
            "base_price": 0.12,
            "description": "Microsoft services"
        },
        {
            "name": "amazon",
            "display_name": "Amazon",
            "category": "ecommerce",
            "popularity": 90,
            "base_price": 0.15,
            "description": "E-commerce and cloud services"
        },
        {
            "name": "uber",
            "display_name": "Uber",
            "category": "transport",
            "popularity": 70,
            "base_price": 0.18,
            "description": "Ride sharing service"
        },
        {
            "name": "lyft",
            "display_name": "Lyft",
            "category": "transport",
            "popularity": 60,
            "base_price": 0.18,
            "description": "Ride sharing service"
        },
        {
            "name": "doordash",
            "display_name": "DoorDash",
            "category": "food",
            "popularity": 75,
            "base_price": 0.16,
            "description": "Food delivery service"
        },
        {
            "name": "grubhub",
            "display_name": "Grubhub",
            "category": "food",
            "popularity": 65,
            "base_price": 0.16,
            "description": "Food delivery service"
        },
        {
            "name": "netflix",
            "display_name": "Netflix",
            "category": "entertainment",
            "popularity": 85,
            "base_price": 0.14,
            "description": "Streaming service"
        },
        {
            "name": "spotify",
            "display_name": "Spotify",
            "category": "entertainment",
            "popularity": 80,
            "base_price": 0.14,
            "description": "Music streaming service"
        },
        {
            "name": "tiktok",
            "display_name": "TikTok",
            "category": "social",
            "popularity": 85,
            "base_price": 0.20,
            "description": "Short video platform"
        },
        {
            "name": "snapchat",
            "display_name": "Snapchat",
            "category": "social",
            "popularity": 70,
            "base_price": 0.18,
            "description": "Multimedia messaging"
        },
        {
            "name": "linkedin",
            "display_name": "LinkedIn",
            "category": "professional",
            "popularity": 75,
            "base_price": 0.16,
            "description": "Professional networking"
        },
        {
            "name": "github",
            "display_name": "GitHub",
            "category": "tech",
            "popularity": 70,
            "base_price": 0.12,
            "description": "Code repository platform"
        },
        {
            "name": "paypal",
            "display_name": "PayPal",
            "category": "finance",
            "popularity": 80,
            "base_price": 0.20,
            "description": "Payment service"
        },
        {
            "name": "venmo",
            "display_name": "Venmo",
            "category": "finance",
            "popularity": 70,
            "base_price": 0.18,
            "description": "Peer-to-peer payments"
        },
        {
            "name": "cashapp",
            "display_name": "Cash App",
            "category": "finance",
            "popularity": 75,
            "base_price": 0.18,
            "description": "Mobile payment service"
        },
        {
            "name": "coinbase",
            "display_name": "Coinbase",
            "category": "crypto",
            "popularity": 60,
            "base_price": 0.25,
            "description": "Cryptocurrency exchange"
        },
        {
            "name": "binance",
            "display_name": "Binance",
            "category": "crypto",
            "popularity": 55,
            "base_price": 0.25,
            "description": "Cryptocurrency exchange"
        },
        {
            "name": "airbnb",
            "display_name": "Airbnb",
            "category": "travel",
            "popularity": 70,
            "base_price": 0.16,
            "description": "Home sharing platform"
        },
        {
            "name": "booking",
            "display_name": "Booking.com",
            "category": "travel",
            "popularity": 65,
            "base_price": 0.16,
            "description": "Hotel booking service"
        }
    ]

    # Sort by popularity (most popular first)
    services.sort(key=lambda x: x["popularity"], reverse=True)

    return {
        "services": services,
        "total": len(services),
        "country": country.upper(),
        "area_code": areaCode,
        "categories": list(set(s["category"] for s in services))
    }
