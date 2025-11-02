"""Countries API router for TextVerified country information."""
from fastapi import APIRouter
from typing import List, Dict, Any


router = APIRouter(prefix="/countries", tags=["Countries"])

@router.get("/")
async def get_available_countries() -> Dict[str, Any]:
    """Get all available countries with pricing and capabilities."""
    try:
        # Use comprehensive TextVerified country data from assessment
        countries = get_textverified_countries()
        
        return {
            "countries": countries,
            "total_count": len(countries),
            "regions": get_regions_summary(countries)
        }
        
    except Exception as e:
        return {"error": f"Failed to fetch countries: {str(e)}", "countries": []}

@router.get("/popular")
async def get_popular_countries() -> Dict[str, Any]:
    """Get most popular countries for verification (Phase 1 priority)."""
    popular_codes = [
        "US", "GB", "DE", "FR", "CA", "AU", "NL", "SE", "JP", "SG", 
        "AE", "SA", "IN", "BR", "RU", "PL", "IT", "ES", "KR", "CH"
    ]
    
    all_countries = await get_available_countries()
    popular_countries = [
        country for country in all_countries["countries"]
        if country["code"] in popular_codes
    ]
    
    # Sort by tier and multiplier
    popular_countries.sort(key=lambda x: (x["tier"] == "Premium", x["price_multiplier"]), reverse=True)
    
    return {
        "countries": popular_countries,
        "total_count": len(popular_countries)
    }

@router.get("/regions")
async def get_countries_by_region() -> Dict[str, Any]:
    """Get countries organized by regions with continent structure."""
    all_countries = await get_available_countries()
    
    regions = {}
    for country in all_countries["countries"]:
        region = country["region"]
        if region not in regions:
            regions[region] = []
        regions[region].append(country)
    
    # Sort countries within each region by tier then name
    for region in regions:
        regions[region].sort(key=lambda x: (x["tier"] != "Premium", x["name"]))
    
    return {
        "regions": regions,
        "region_count": len(regions),
        "total_countries": sum(len(countries) for countries in regions.values())
    }

@router.get("/{country_code}")
async def get_country_details(country_code: str) -> Dict[str, Any]:
    """Get detailed information for a specific country."""
    all_countries = await get_available_countries()
    
    country = next(
        (c for c in all_countries["countries"] if c["code"] == country_code.upper()),
        None
    )
    
    if not country:
        return {"error": f"Country {country_code} not found"}
    
    # Add additional details
    country_details = {
        **country,
        "services_available": get_country_services(country_code),
        "estimated_delivery_time": get_delivery_time(country_code),
        "success_rate": get_success_rate(country_code)
    }
    
    return country_details



def get_textverified_countries() -> List[Dict[str, Any]]:
    """Get comprehensive TextVerified country data from assessment."""
    countries = [
        # North America (3 countries)
        {"code": "US", "name": "United States", "price_multiplier": 1.0, "voice_supported": True, "region": "North America", "tier": "Standard"},
        {"code": "CA", "name": "Canada", "price_multiplier": 1.1, "voice_supported": True, "region": "North America", "tier": "Standard"},
        {"code": "MX", "name": "Mexico", "price_multiplier": 0.4, "voice_supported": False, "region": "North America", "tier": "Economy"},
        
        # Europe (29 countries)
        {"code": "GB", "name": "United Kingdom", "price_multiplier": 1.0, "voice_supported": True, "region": "Europe", "tier": "Standard"},
        {"code": "DE", "name": "Germany", "price_multiplier": 1.0, "voice_supported": True, "region": "Europe", "tier": "Standard"},
        {"code": "FR", "name": "France", "price_multiplier": 1.0, "voice_supported": True, "region": "Europe", "tier": "Standard"},
        {"code": "NL", "name": "Netherlands", "price_multiplier": 1.0, "voice_supported": True, "region": "Europe", "tier": "Standard"},
        {"code": "CH", "name": "Switzerland", "price_multiplier": 1.8, "voice_supported": True, "region": "Europe", "tier": "Premium"},
        {"code": "AT", "name": "Austria", "price_multiplier": 1.0, "voice_supported": True, "region": "Europe", "tier": "Standard"},
        {"code": "BE", "name": "Belgium", "price_multiplier": 1.0, "voice_supported": True, "region": "Europe", "tier": "Standard"},
        {"code": "IE", "name": "Ireland", "price_multiplier": 1.0, "voice_supported": True, "region": "Europe", "tier": "Standard"},
        {"code": "LU", "name": "Luxembourg", "price_multiplier": 1.2, "voice_supported": True, "region": "Europe", "tier": "Premium"},
        {"code": "SE", "name": "Sweden", "price_multiplier": 1.5, "voice_supported": True, "region": "Europe", "tier": "Premium"},
        {"code": "NO", "name": "Norway", "price_multiplier": 1.6, "voice_supported": True, "region": "Europe", "tier": "Premium"},
        {"code": "FI", "name": "Finland", "price_multiplier": 1.3, "voice_supported": True, "region": "Europe", "tier": "Premium"},
        {"code": "DK", "name": "Denmark", "price_multiplier": 1.4, "voice_supported": True, "region": "Europe", "tier": "Premium"},
        {"code": "IS", "name": "Iceland", "price_multiplier": 1.7, "voice_supported": True, "region": "Europe", "tier": "Premium"},
        {"code": "IT", "name": "Italy", "price_multiplier": 0.9, "voice_supported": True, "region": "Europe", "tier": "Standard"},
        {"code": "ES", "name": "Spain", "price_multiplier": 0.9, "voice_supported": True, "region": "Europe", "tier": "Standard"},
        {"code": "PT", "name": "Portugal", "price_multiplier": 0.8, "voice_supported": True, "region": "Europe", "tier": "Standard"},
        {"code": "MT", "name": "Malta", "price_multiplier": 0.9, "voice_supported": False, "region": "Europe", "tier": "Standard"},
        {"code": "CY", "name": "Cyprus", "price_multiplier": 0.8, "voice_supported": False, "region": "Europe", "tier": "Standard"},
        {"code": "PL", "name": "Poland", "price_multiplier": 0.6, "voice_supported": True, "region": "Europe", "tier": "Economy"},
        {"code": "CZ", "name": "Czech Republic", "price_multiplier": 0.6, "voice_supported": True, "region": "Europe", "tier": "Economy"},
        {"code": "HU", "name": "Hungary", "price_multiplier": 0.6, "voice_supported": True, "region": "Europe", "tier": "Economy"},
        {"code": "RO", "name": "Romania", "price_multiplier": 0.5, "voice_supported": False, "region": "Europe", "tier": "Economy"},
        {"code": "BG", "name": "Bulgaria", "price_multiplier": 0.5, "voice_supported": False, "region": "Europe", "tier": "Economy"},
        {"code": "HR", "name": "Croatia", "price_multiplier": 0.6, "voice_supported": False, "region": "Europe", "tier": "Economy"},
        {"code": "SI", "name": "Slovenia", "price_multiplier": 0.7, "voice_supported": False, "region": "Europe", "tier": "Economy"},
        {"code": "SK", "name": "Slovakia", "price_multiplier": 0.6, "voice_supported": False, "region": "Europe", "tier": "Economy"},
        {"code": "LT", "name": "Lithuania", "price_multiplier": 0.5, "voice_supported": False, "region": "Europe", "tier": "Economy"},
        {"code": "LV", "name": "Latvia", "price_multiplier": 0.5, "voice_supported": False, "region": "Europe", "tier": "Economy"},
        {"code": "EE", "name": "Estonia", "price_multiplier": 0.5, "voice_supported": False, "region": "Europe", "tier": "Economy"},
        
        # Asia-Pacific (16 countries)
        {"code": "JP", "name": "Japan", "price_multiplier": 1.5, "voice_supported": True, "region": "Asia-Pacific", "tier": "Premium"},
        {"code": "KR", "name": "South Korea", "price_multiplier": 1.2, "voice_supported": True, "region": "Asia-Pacific", "tier": "Premium"},
        {"code": "SG", "name": "Singapore", "price_multiplier": 1.3, "voice_supported": True, "region": "Asia-Pacific", "tier": "Premium"},
        {"code": "AU", "name": "Australia", "price_multiplier": 1.4, "voice_supported": True, "region": "Asia-Pacific", "tier": "Premium"},
        {"code": "HK", "name": "Hong Kong", "price_multiplier": 1.0, "voice_supported": True, "region": "Asia-Pacific", "tier": "Standard"},
        {"code": "TW", "name": "Taiwan", "price_multiplier": 0.8, "voice_supported": False, "region": "Asia-Pacific", "tier": "Standard"},
        {"code": "MY", "name": "Malaysia", "price_multiplier": 0.5, "voice_supported": False, "region": "Asia-Pacific", "tier": "Economy"},
        {"code": "TH", "name": "Thailand", "price_multiplier": 0.4, "voice_supported": False, "region": "Asia-Pacific", "tier": "Economy"},
        {"code": "PH", "name": "Philippines", "price_multiplier": 0.3, "voice_supported": False, "region": "Asia-Pacific", "tier": "Economy"},
        {"code": "ID", "name": "Indonesia", "price_multiplier": 0.3, "voice_supported": False, "region": "Asia-Pacific", "tier": "Economy"},
        {"code": "VN", "name": "Vietnam", "price_multiplier": 0.3, "voice_supported": False, "region": "Asia-Pacific", "tier": "Economy"},
        {"code": "IN", "name": "India", "price_multiplier": 0.2, "voice_supported": False, "region": "Asia-Pacific", "tier": "Economy"},
        {"code": "BD", "name": "Bangladesh", "price_multiplier": 0.2, "voice_supported": False, "region": "Asia-Pacific", "tier": "Economy"},
        {"code": "PK", "name": "Pakistan", "price_multiplier": 0.2, "voice_supported": False, "region": "Asia-Pacific", "tier": "Economy"},
        {"code": "LK", "name": "Sri Lanka", "price_multiplier": 0.2, "voice_supported": False, "region": "Asia-Pacific", "tier": "Economy"},
        {"code": "NP", "name": "Nepal", "price_multiplier": 0.2, "voice_supported": False, "region": "Asia-Pacific", "tier": "Economy"},
        {"code": "CN", "name": "China", "price_multiplier": 0.8, "voice_supported": False, "region": "Asia-Pacific", "tier": "Standard"},
        
        # Latin America (11 countries)
        {"code": "BR", "name": "Brazil", "price_multiplier": 0.4, "voice_supported": True, "region": "Latin America", "tier": "Economy"},
        {"code": "AR", "name": "Argentina", "price_multiplier": 0.3, "voice_supported": False, "region": "Latin America", "tier": "Economy"},
        {"code": "CO", "name": "Colombia", "price_multiplier": 0.3, "voice_supported": False, "region": "Latin America", "tier": "Economy"},
        {"code": "PE", "name": "Peru", "price_multiplier": 0.3, "voice_supported": False, "region": "Latin America", "tier": "Economy"},
        {"code": "CL", "name": "Chile", "price_multiplier": 0.4, "voice_supported": False, "region": "Latin America", "tier": "Economy"},
        {"code": "UY", "name": "Uruguay", "price_multiplier": 0.4, "voice_supported": False, "region": "Latin America", "tier": "Economy"},
        {"code": "PY", "name": "Paraguay", "price_multiplier": 0.3, "voice_supported": False, "region": "Latin America", "tier": "Economy"},
        {"code": "BO", "name": "Bolivia", "price_multiplier": 0.3, "voice_supported": False, "region": "Latin America", "tier": "Economy"},
        {"code": "EC", "name": "Ecuador", "price_multiplier": 0.3, "voice_supported": False, "region": "Latin America", "tier": "Economy"},
        {"code": "VE", "name": "Venezuela", "price_multiplier": 0.3, "voice_supported": False, "region": "Latin America", "tier": "Economy"},
        
        # Middle East & Africa (11 countries)
        {"code": "ZA", "name": "South Africa", "price_multiplier": 0.5, "voice_supported": True, "region": "Middle East & Africa", "tier": "Economy"},
        {"code": "NG", "name": "Nigeria", "price_multiplier": 0.3, "voice_supported": False, "region": "Middle East & Africa", "tier": "Economy"},
        {"code": "KE", "name": "Kenya", "price_multiplier": 0.3, "voice_supported": False, "region": "Middle East & Africa", "tier": "Economy"},
        {"code": "GH", "name": "Ghana", "price_multiplier": 0.3, "voice_supported": False, "region": "Middle East & Africa", "tier": "Economy"},
        {"code": "EG", "name": "Egypt", "price_multiplier": 0.4, "voice_supported": False, "region": "Middle East & Africa", "tier": "Economy"},
        {"code": "MA", "name": "Morocco", "price_multiplier": 0.4, "voice_supported": False, "region": "Middle East & Africa", "tier": "Economy"},
        {"code": "TN", "name": "Tunisia", "price_multiplier": 0.4, "voice_supported": False, "region": "Middle East & Africa", "tier": "Economy"},
        {"code": "DZ", "name": "Algeria", "price_multiplier": 0.4, "voice_supported": False, "region": "Middle East & Africa", "tier": "Economy"},
        {"code": "AE", "name": "United Arab Emirates", "price_multiplier": 0.8, "voice_supported": True, "region": "Middle East & Africa", "tier": "Standard"},
        {"code": "SA", "name": "Saudi Arabia", "price_multiplier": 0.6, "voice_supported": True, "region": "Middle East & Africa", "tier": "Economy"},
        {"code": "IL", "name": "Israel", "price_multiplier": 1.0, "voice_supported": True, "region": "Middle East & Africa", "tier": "Standard"},
        {"code": "QA", "name": "Qatar", "price_multiplier": 0.8, "voice_supported": False, "region": "Middle East & Africa", "tier": "Standard"},
        {"code": "KW", "name": "Kuwait", "price_multiplier": 0.7, "voice_supported": False, "region": "Middle East & Africa", "tier": "Economy"},
        {"code": "BH", "name": "Bahrain", "price_multiplier": 0.7, "voice_supported": False, "region": "Middle East & Africa", "tier": "Economy"},
        {"code": "OM", "name": "Oman", "price_multiplier": 0.6, "voice_supported": False, "region": "Middle East & Africa", "tier": "Economy"},
        {"code": "JO", "name": "Jordan", "price_multiplier": 0.5, "voice_supported": False, "region": "Middle East & Africa", "tier": "Economy"},
        {"code": "LB", "name": "Lebanon", "price_multiplier": 0.5, "voice_supported": False, "region": "Middle East & Africa", "tier": "Economy"},
        {"code": "IQ", "name": "Iraq", "price_multiplier": 0.4, "voice_supported": False, "region": "Middle East & Africa", "tier": "Economy"},
        
        # CIS (5 countries)
        {"code": "RU", "name": "Russia", "price_multiplier": 0.5, "voice_supported": True, "region": "CIS", "tier": "Economy"},
        {"code": "UA", "name": "Ukraine", "price_multiplier": 0.4, "voice_supported": False, "region": "CIS", "tier": "Economy"},
        {"code": "BY", "name": "Belarus", "price_multiplier": 0.4, "voice_supported": False, "region": "CIS", "tier": "Economy"},
        {"code": "KZ", "name": "Kazakhstan", "price_multiplier": 0.4, "voice_supported": False, "region": "CIS", "tier": "Economy"},
        {"code": "UZ", "name": "Uzbekistan", "price_multiplier": 0.3, "voice_supported": False, "region": "CIS", "tier": "Economy"},
        {"code": "TR", "name": "Turkey", "price_multiplier": 0.5, "voice_supported": True, "region": "CIS", "tier": "Economy"},
    ]
    
    return countries





def get_regions_summary(countries: List[Dict]) -> Dict[str, int]:
    """Get summary of countries per region."""
    regions = {}
    for country in countries:
        region = country["region"]
        regions[region] = regions.get(region, 0) + 1
    return regions

def get_country_services(country_code: str) -> List[str]:
    """Get available services for country."""
    # All countries support basic services
    basic_services = ["telegram", "whatsapp", "discord", "google", "instagram"]
    
    # Premium countries support additional services
    premium_countries = ["US", "GB", "DE", "FR", "CA", "AU", "JP", "SG"]
    if country_code in premium_countries:
        return basic_services + ["paypal", "microsoft", "amazon", "netflix"]
    
    return basic_services

def get_delivery_time(country_code: str) -> str:
    """Get estimated SMS delivery time."""
    fast_countries = ["US", "GB", "DE", "FR", "CA", "AU", "NL", "SE"]
    if country_code in fast_countries:
        return "1-30 seconds"
    else:
        return "30-120 seconds"

def get_success_rate(country_code: str) -> float:
    """Get success rate for country."""
    premium_countries = ["US", "GB", "DE", "FR", "CA", "AU", "JP", "SG"]
    if country_code in premium_countries:
        return 98.5
    else:
        return 95.0

