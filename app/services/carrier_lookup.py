"""
Carrier Lookup Service - Real Carrier Verification
Uses Numverify API for carrier identification (60-75% accuracy)
"""

import asyncio
import logging
import os
from typing import Dict, Optional

import aiohttp

logger = logging.getLogger(__name__)

# Numverify API configuration
NUMVERIFY_BASE_URL = "http://apilayer.net/api/validate"
NUMVERIFY_TIMEOUT = 5.0  # seconds


class CarrierLookupService:
    """Service for real carrier verification via Numverify API"""

    def __init__(self):
        self.api_key = os.getenv("NUMVERIFY_API_KEY")
        self.enabled = bool(self.api_key)

        if not self.enabled:
            logger.warning("Numverify API disabled - missing NUMVERIFY_API_KEY")
        else:
            logger.info("Numverify carrier lookup service initialized")

    async def lookup_carrier(self, phone_number: str) -> Dict:
        """
        Look up real carrier for phone number via Numverify API.

        Args:
            phone_number: Phone number in E.164 format (e.g., +14155551234)

        Returns:
            {
                "success": bool,
                "carrier": str,  # Normalized carrier name
                "raw_carrier": str,  # Original carrier name from API
                "line_type": str,  # "mobile", "landline", etc.
                "valid": bool,
                "error": str (optional)
            }
        """
        if not self.enabled:
            return {
                "success": False,
                "carrier": "unknown",
                "valid": False,
                "error": "Numverify API is disabled - missing API key",
            }

        # Clean phone number (remove + prefix for API)
        clean_number = phone_number.replace("+", "").replace(" ", "").replace("-", "")

        try:
            async with aiohttp.ClientSession() as session:
                params = {
                    "access_key": self.api_key,
                    "number": clean_number,
                    "format": 1,  # JSON format
                }

                async with session.get(
                    NUMVERIFY_BASE_URL,
                    params=params,
                    timeout=aiohttp.ClientTimeout(total=NUMVERIFY_TIMEOUT),
                ) as response:

                    if response.status != 200:
                        error_text = await response.text()
                        logger.error(
                            f"Numverify API error {response.status}: {error_text}"
                        )
                        return {
                            "success": False,
                            "carrier": "unknown",
                            "valid": False,
                            "error": f"API error: {response.status}",
                        }

                    data = await response.json()

                    # Check if API returned an error
                    if "error" in data:
                        error_code = data["error"].get("code")
                        error_info = data["error"].get("info", "Unknown error")
                        if error_code == 104:
                            logger.error(
                                f"NUMVERIFY QUOTA EXHAUSTED — carrier lookup disabled until next billing cycle. ({error_info})"
                            )
                        elif error_code in (101, 102, 103):
                            logger.error(
                                f"NUMVERIFY AUTH FAILURE (code {error_code}) — check NUMVERIFY_API_KEY on Render. ({error_info})"
                            )
                        else:
                            logger.warning(
                                f"Numverify API error {error_code}: {error_info}"
                            )
                        return {
                            "success": False,
                            "carrier": "unknown",
                            "valid": False,
                            "error": error_info,
                        }

                    # Check if number is valid
                    if not data.get("valid", False):
                        return {
                            "success": False,
                            "carrier": "unknown",
                            "valid": False,
                            "error": "Invalid phone number",
                        }

                    # Extract carrier information
                    raw_carrier = data.get("carrier", "Unknown")
                    line_type = data.get("line_type", "unknown")

                    # Normalize carrier name
                    normalized_carrier = self.normalize_carrier(raw_carrier)

                    logger.info(
                        f"Carrier lookup success: {phone_number} -> "
                        f"{normalized_carrier} ({raw_carrier}, {line_type})"
                    )

                    return {
                        "success": True,
                        "carrier": normalized_carrier,
                        "raw_carrier": raw_carrier,
                        "line_type": line_type,
                        "valid": True,
                    }

        except asyncio.TimeoutError:
            logger.warning(f"Numverify API timeout for {phone_number}")
            return {
                "success": False,
                "carrier": "unknown",
                "valid": False,
                "error": "API timeout",
            }
        except Exception as e:
            logger.error(f"Carrier lookup failed for {phone_number}: {e}")
            return {
                "success": False,
                "carrier": "unknown",
                "valid": False,
                "error": str(e),
            }

    def normalize_carrier(self, carrier_name: Optional[str]) -> str:
        """
        Normalize carrier name to standard format.

        Maps various carrier name formats to our standard names:
        - verizon, tmobile, att, sprint, etc.

        Returns "unknown" if carrier cannot be identified.
        """
        if not carrier_name:
            return "unknown"

        # Convert to lowercase for comparison
        carrier_lower = carrier_name.lower()

        # Verizon variants
        if "verizon" in carrier_lower:
            return "verizon"

        # T-Mobile variants (includes Sprint after merger)
        if (
            "t-mobile" in carrier_lower
            or "tmobile" in carrier_lower
            or "t mobile" in carrier_lower
        ):
            return "tmobile"

        # AT&T variants
        if "at&t" in carrier_lower or "att" in carrier_lower or "at&t" in carrier_lower:
            return "att"

        # Sprint (legacy, now T-Mobile)
        if "sprint" in carrier_lower:
            return "tmobile"  # Sprint merged with T-Mobile

        # US Cellular
        if "us cellular" in carrier_lower or "uscellular" in carrier_lower:
            return "us_cellular"

        # Metro by T-Mobile
        if "metro" in carrier_lower:
            return "metro"

        # Boost Mobile
        if "boost" in carrier_lower:
            return "boost"

        # Cricket Wireless
        if "cricket" in carrier_lower:
            return "cricket"

        # Unknown carrier
        logger.debug(f"Unknown carrier name: {carrier_name}")
        return "unknown"
