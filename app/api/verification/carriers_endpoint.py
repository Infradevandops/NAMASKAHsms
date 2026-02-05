"""Carriers endpoint for verification system."""


from fastapi import APIRouter

router = APIRouter(prefix="/api/verification", tags=["Carriers"])


@router.get("/carriers/{country}")
async def get_carriers(country: str):
    """Get available carriers for a country.

    Currently supports US carriers only.
    """
if country.upper() != "US":
        return {"carriers": [], "total": 0, "message": "Only US carriers supported"}

    # Major US carriers
    us_carriers = [
        {
            "code": "verizon",
            "name": "Verizon",
            "display_name": "Verizon Wireless",
            "type": "major",
            "coverage": "nationwide",
            "reliability": 95,
            "premium": 0.05,
            "description": "Largest US wireless carrier"
        },
        {
            "code": "att",
            "name": "AT&T",
            "display_name": "AT&T Wireless",
            "type": "major",
            "coverage": "nationwide",
            "reliability": 92,
            "premium": 0.04,
            "description": "Second largest US carrier"
        },
        {
            "code": "tmobile",
            "name": "T-Mobile",
            "display_name": "T-Mobile US",
            "type": "major",
            "coverage": "nationwide",
            "reliability": 90,
            "premium": 0.03,
            "description": "Third largest US carrier"
        },
        {
            "code": "sprint",
            "name": "Sprint",
            "display_name": "Sprint (T-Mobile)",
            "type": "major",
            "coverage": "nationwide",
            "reliability": 85,
            "premium": 0.02,
            "description": "Now part of T-Mobile network"
        },
        {
            "code": "uscellular",
            "name": "US Cellular",
            "display_name": "U.S. Cellular",
            "type": "regional",
            "coverage": "regional",
            "reliability": 80,
            "premium": 0.01,
            "description": "Regional carrier serving rural areas"
        },
        {
            "code": "cricket",
            "name": "Cricket",
            "display_name": "Cricket Wireless",
            "type": "mvno",
            "coverage": "nationwide",
            "reliability": 85,
            "premium": 0.00,
            "description": "AT&T prepaid brand"
        },
        {
            "code": "metropcs",
            "name": "Metro PCS",
            "display_name": "Metro by T-Mobile",
            "type": "mvno",
            "coverage": "nationwide",
            "reliability": 82,
            "premium": 0.00,
            "description": "T-Mobile prepaid brand"
        },
        {
            "code": "boost",
            "name": "Boost Mobile",
            "display_name": "Boost Mobile",
            "type": "mvno",
            "coverage": "nationwide",
            "reliability": 78,
            "premium": 0.00,
            "description": "Prepaid carrier on multiple networks"
        },
        {
            "code": "virgin",
            "name": "Virgin Mobile",
            "display_name": "Virgin Mobile USA",
            "type": "mvno",
            "coverage": "nationwide",
            "reliability": 75,
            "premium": 0.00,
            "description": "Prepaid carrier"
        },
        {
            "code": "straighttalk",
            "name": "Straight Talk",
            "display_name": "Straight Talk Wireless",
            "type": "mvno",
            "coverage": "nationwide",
            "reliability": 80,
            "premium": 0.00,
            "description": "Walmart's wireless service"
        },
        {
            "code": "tracfone",
            "name": "TracFone",
            "display_name": "TracFone Wireless",
            "type": "mvno",
            "coverage": "nationwide",
            "reliability": 75,
            "premium": 0.00,
            "description": "Prepaid wireless service"
        },
        {
            "code": "mint",
            "name": "Mint Mobile",
            "display_name": "Mint Mobile",
            "type": "mvno",
            "coverage": "nationwide",
            "reliability": 85,
            "premium": 0.00,
            "description": "T-Mobile MVNO with bulk plans"
        },
        {
            "code": "visible",
            "name": "Visible",
            "display_name": "Visible Wireless",
            "type": "mvno",
            "coverage": "nationwide",
            "reliability": 88,
            "premium": 0.01,
            "description": "Verizon's digital-first brand"
        },
        {
            "code": "xfinity",
            "name": "Xfinity Mobile",
            "display_name": "Xfinity Mobile",
            "type": "mvno",
            "coverage": "nationwide",
            "reliability": 90,
            "premium": 0.02,
            "description": "Comcast's wireless service"
        },
        {
            "code": "spectrum",
            "name": "Spectrum Mobile",
            "display_name": "Spectrum Mobile",
            "type": "mvno",
            "coverage": "nationwide",
            "reliability": 88,
            "premium": 0.02,
            "description": "Charter's wireless service"
        },
        {
            "code": "google",
            "name": "Google Fi",
            "display_name": "Google Fi Wireless",
            "type": "mvno",
            "coverage": "nationwide",
            "reliability": 85,
            "premium": 0.03,
            "description": "Google's wireless service"
        }
    ]

    # Sort by reliability (most reliable first)
    us_carriers.sort(key=lambda x: x["reliability"], reverse=True)

    return {
        "carriers": us_carriers,
        "total": len(us_carriers),
        "country": country.upper(),
        "types": {
            "major": [c for c in us_carriers if c["type"] == "major"],
            "regional": [c for c in us_carriers if c["type"] == "regional"],
            "mvno": [c for c in us_carriers if c["type"] == "mvno"]
        }
    }
