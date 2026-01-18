"""Multi - region deployment and load balancing."""

import asyncio
from typing import Dict
from dataclasses import dataclass


@dataclass
class Region:
    name: str
    endpoint: str
    latency: float = 0.0
    active: bool = True
    capacity: int = 100


class RegionManager:
    """Manages multi - region deployment and routing."""

    def __init__(self):
        self.regions = {
            "us - east": Region("US East", "https://us - east.namaskah.app", active=True),
            "us - west": Region("US West", "https://us - west.namaskah.app", active=True),
            "eu - west": Region("EU West", "https://eu - west.namaskah.app", active=True),
            "asia - pacific": Region("Asia Pacific", "https://ap.namaskah.app", active=True),
        }
        self.primary_region = "us - east"

    async def get_optimal_region(self, user_location: str = None) -> str:
        """Get optimal region based on user location and performance."""
        if user_location:
            # Geographic routing
            location_mapping = {
                "US": "us - east",
                "CA": "us - west",
                "GB": "eu - west",
                "DE": "eu - west",
                "FR": "eu - west",
                "JP": "asia - pacific",
                "AU": "asia - pacific",
                "SG": "asia - pacific",
            }

            preferred = location_mapping.get(user_location, self.primary_region)
            if self.regions[preferred].active:
                return preferred

        # Fallback to lowest latency active region
        active_regions = {k: v for k, v in self.regions.items() if v.active}
        if not active_regions:
            return self.primary_region

        return min(active_regions.keys(), key=lambda r: self.regions[r].latency)

    async def health_check_regions(self) -> Dict[str, bool]:
        """Perform health checks on all regions."""
        results = {}

        for region_id, region in self.regions.items():
            try:
                # Simulate health check (in production, use actual HTTP checks)
                await asyncio.sleep(0.1)  # Simulate network delay
                results[region_id] = True
                region.active = True
            except Exception:
                results[region_id] = False
                region.active = False

        return results

    def get_region_status(self) -> Dict:
        """Get status of all regions."""
        return {
            region_id: {
                "name": region.name,
                "endpoint": region.endpoint,
                "active": region.active,
                "latency": region.latency,
                "capacity": region.capacity,
            }
            for region_id, region in self.regions.items()
        }


# Global region manager instance
region_manager = RegionManager()
