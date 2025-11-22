"""CDN and static asset management service."""
from typing import Dict


class CDNService:
    """CDN management for global content delivery."""

    def __init__(self):
        self.cdn_endpoints = {
            "cloudflare": "https://cdn.namaskah.app",
            "aws_cloudfront": "https://d1234567890.cloudfront.net",
            "fastly": "https://namaskah.global.ssl.fastly.net"
        }
        self.primary_cdn = "cloudflare"

    def get_asset_url(self, asset_path: str, region: str = None) -> str:
        """Get optimized CDN URL for asset."""
        base_url = self.cdn_endpoints[self.primary_cdn]

        # Add region - specific optimization
        if region:
            region_prefix = {
                "us - east": "us",
                "us - west": "us",
                "eu - west": "eu",
                "asia - pacific": "ap"
            }.get(region, "global")

            return f"{base_url}/{region_prefix}/{asset_path}"

        return f"{base_url}/{asset_path}"

    def get_cdn_config(self) -> Dict:
        """Get CDN configuration for frontend."""
        return {
            "primary_endpoint": self.cdn_endpoints[self.primary_cdn],
            "fallback_endpoints": [
                url for key, url in self.cdn_endpoints.items()
                if key != self.primary_cdn
            ],
            "cache_headers": {
                "Cache - Control": "public, max - age = 31536000",
                "CDN - Cache-Control": "max - age = 31536000"
            }
        }


# Global CDN service instance
cdn_service = CDNService()
