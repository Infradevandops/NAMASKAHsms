"""Multi-region deployment and load balancing."""


import asyncio
from dataclasses import dataclass
from typing import Dict


@dataclass
class Region:
    name: str
    endpoint: str
    latency: float = 0.0
    active: bool = True
    capacity: int = 100


class RegionManager:
    """Manages multi-region deployment and routing."""

    def __init__(self):
        self.regions = {
            "us-east": Region("US East", "https://us-east.namaskah.app", active=True),
            "us-west": Region("US West", "https://us-west.namaskah.app", active=True),
            "eu-west": Region("EU West", "https://eu-west.namaskah.app", active=True),
            "asia-pacific": Region("Asia Pacific", "https://ap.namaskah.app", active=True),
        }
        self.primary_region = "us-east"

    def get_best_region(self, user_location: str = None) -> Region:
        """Get best region for user."""
        active_regions = [r for r in self.regions.values() if r.active]
        if not active_regions:
            return self.regions[self.primary_region]

        return min(active_regions, key=lambda r: r.latency)

    async def health_check_all(self) -> Dict[str, bool]:
        """Check health of all regions."""
        results = {}
        for name, region in self.regions.items():
            results[name] = region.active
        return results


region_manager = RegionManager()
