import math
from typing import List, Dict, Any

# A representative sample of NANPA area codes, containing major US cities.
# In a full system, this would contain all ~370 active US area codes.
NANPA_DATA: Dict[str, Dict[str, Any]] = {
    # Los Angeles Metro
    "213": {"major_city": "Los Angeles", "state": "CA", "lat": 34.0522, "lng": -118.2437, "metro": "Los Angeles"},
    "323": {"major_city": "Los Angeles", "state": "CA", "lat": 34.0522, "lng": -118.2437, "metro": "Los Angeles"},
    "310": {"major_city": "Los Angeles", "state": "CA", "lat": 34.0522, "lng": -118.2437, "metro": "Los Angeles"},
    "818": {"major_city": "Burbank", "state": "CA", "lat": 34.1808, "lng": -118.3090, "metro": "Los Angeles"},
    "626": {"major_city": "Pasadena", "state": "CA", "lat": 34.1478, "lng": -118.1445, "metro": "Los Angeles"},
    "424": {"major_city": "Los Angeles", "state": "CA", "lat": 33.9000, "lng": -118.2500, "metro": "Los Angeles"},
    "747": {"major_city": "Burbank", "state": "CA", "lat": 34.2000, "lng": -118.4000, "metro": "Los Angeles"},
    "562": {"major_city": "Long Beach", "state": "CA", "lat": 33.7701, "lng": -118.1937, "metro": "Los Angeles"},
    # SF Bay Area
    "415": {"major_city": "San Francisco", "state": "CA", "lat": 37.7749, "lng": -122.4194, "metro": "San Francisco"},
    "628": {"major_city": "San Francisco", "state": "CA", "lat": 37.7749, "lng": -122.4194, "metro": "San Francisco"},
    "650": {"major_city": "San Mateo", "state": "CA", "lat": 37.5630, "lng": -122.3255, "metro": "San Francisco"},
    "510": {"major_city": "Oakland", "state": "CA", "lat": 37.8044, "lng": -122.2712, "metro": "San Francisco"},
    # Sacramento
    "916": {"major_city": "Sacramento", "state": "CA", "lat": 38.5816, "lng": -121.4944, "metro": "Sacramento"},
    "279": {"major_city": "Sacramento", "state": "CA", "lat": 38.5816, "lng": -121.4944, "metro": "Sacramento"},
    # New York Metro
    "212": {"major_city": "New York", "state": "NY", "lat": 40.7128, "lng": -74.0060, "metro": "New York"},
    "718": {"major_city": "New York", "state": "NY", "lat": 40.7128, "lng": -74.0060, "metro": "New York"},
    "917": {"major_city": "New York", "state": "NY", "lat": 40.7128, "lng": -74.0060, "metro": "New York"},
    "332": {"major_city": "New York", "state": "NY", "lat": 40.7128, "lng": -74.0060, "metro": "New York"},
    # Miami Metro
    "305": {"major_city": "Miami", "state": "FL", "lat": 25.7617, "lng": -80.1918, "metro": "Miami"},
    "786": {"major_city": "Miami", "state": "FL", "lat": 25.7617, "lng": -80.1918, "metro": "Miami"},
    # Chicago Metro
    "312": {"major_city": "Chicago", "state": "IL", "lat": 41.8781, "lng": -87.6298, "metro": "Chicago"},
    "773": {"major_city": "Chicago", "state": "IL", "lat": 41.8781, "lng": -87.6298, "metro": "Chicago"},
    # Texas
    "214": {"major_city": "Dallas", "state": "TX", "lat": 32.7767, "lng": -96.7970, "metro": "Dallas"},
    "469": {"major_city": "Dallas", "state": "TX", "lat": 32.7767, "lng": -96.7970, "metro": "Dallas"},
    "512": {"major_city": "Austin", "state": "TX", "lat": 30.2672, "lng": -97.7431, "metro": "Austin"},
    "713": {"major_city": "Houston", "state": "TX", "lat": 29.7604, "lng": -95.3698, "metro": "Houston"},
}

def _haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate the great circle distance between two points on the earth (specified in decimal degrees) in miles."""
    # Convert decimal degrees to radians
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])

    # Haversine formula
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
    c = 2 * math.asin(math.sqrt(a))
    r = 3956 # Radius of earth in miles
    return c * r

def get_metro_codes(area_code: str) -> List[str]:
    """Returns all area codes in the same metro area as the provided area code."""
    if area_code not in NANPA_DATA:
        return []
    
    target_metro = NANPA_DATA[area_code]["metro"]
    # Return all area codes matching the metro
    return [code for code, data in NANPA_DATA.items() if data["metro"] == target_metro]

def filter_supported(area_codes: List[str], supported_list: List[str]) -> List[str]:
    """
    Returns area codes that exist in the supported string list.
    supported_list should be the array returned from TextVerified get_area_codes_list.
    """
    # Supported list items might come as pure strings or dicts, we assume pure string list
    # The TextVerified list returns items like {"area_code": "213", "state": "CA"}
    # To be safe, if supported_list is dicts, extract 'area_code', otherwise treat as strings.
    supported_codes = set()
    for item in supported_list:
        if isinstance(item, dict) and "area_code" in item:
            supported_codes.add(str(item["area_code"]))
        else:
            # Maybe it is just string
            supported_codes.add(str(item))
            
    return [code for code in area_codes if code in supported_codes]

def get_nearby(area_code: str, max_results: int = 8) -> List[Dict[str, Any]]:
    """
    Returns nearby area codes up to max_results, tiered by same_city, nearby (<50mi), same_state (>50mi).
    """
    if area_code not in NANPA_DATA:
        return []
        
    target_data = NANPA_DATA[area_code]
    target_lat = target_data["lat"]
    target_lng = target_data["lng"]
    target_metro = target_data["metro"]
    target_state = target_data["state"]

    results = []
    
    for code, data in NANPA_DATA.items():
        if code == area_code:
            continue
            
        dist = _haversine(target_lat, target_lng, data["lat"], data["lng"])
        
        tier = None
        if data["metro"] == target_metro:
            tier = "same_city"
        elif dist < 50:
            tier = "nearby"
        elif data["state"] == target_state:
            tier = "same_state"
            
        if tier:
            results.append({
                "area_code": code,
                "city": data["major_city"],
                "state": data["state"],
                "proximity": tier,
                "distance": dist
            })
            
    # Sort by tier priority then by distance
    tier_order = {"same_city": 0, "nearby": 1, "same_state": 2}
    results.sort(key=lambda x: (tier_order[x["proximity"]], x["distance"]))
    
    return results[:max_results]


async def get_ranked_alternatives(area_code: str, service: str, max_results: int = 8) -> List[Dict[str, Any]]:
    """
    Return ranked alternative area codes for use in AreaCodeUnavailableException.

    Does NOT query the database — geo ranking only. Purchase-intelligence scoring
    happens separately in the /check API endpoint (Phase 3). This keeps the
    purchase path fast and DB-session-free.

    Returns a list of dicts compatible with the frontend alternatives UI:
      [{area_code, city, state, proximity, status, confidence}]
    """
    nearby = get_nearby(area_code, max_results=max_results)
    return [
        {
            "area_code": alt["area_code"],
            "city": alt["city"],
            "state": alt["state"],
            "proximity": alt["proximity"],
            "status": "unknown",     # No DB access here — frontend can re-check via /check
            "confidence": 0.0,
        }
        for alt in nearby
    ]
