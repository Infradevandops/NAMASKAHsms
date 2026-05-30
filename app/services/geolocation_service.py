import logging
from typing import Optional

from fastapi import Request

logger = logging.getLogger(__name__)


class GeolocationService:
    @staticmethod
    def detect_country(request: Request) -> str:
        """
        Detect the user's country from the request.
        For production, this prioritizes Cloudflare/Proxy headers like CF-IPCountry.
        Falls back to 'US' if unknown.
        """
        # 1. Check Cloudflare header
        cf_country = request.headers.get("CF-IPCountry")
        if cf_country and cf_country != "XX":
            return cf_country.upper()

        # 2. Check X-Vercel-IP-Country or similar common CDN headers
        vercel_country = request.headers.get("x-vercel-ip-country")
        if vercel_country:
            return vercel_country.upper()

        # 3. Check CloudFront header
        cf_viewer_country = request.headers.get("CloudFront-Viewer-Country")
        if cf_viewer_country:
            return cf_viewer_country.upper()

        # Fallback to US if local or detection failed
        return "US"


geolocation_service = GeolocationService()
