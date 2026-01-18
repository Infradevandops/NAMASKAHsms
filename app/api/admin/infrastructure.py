"""Infrastructure management API endpoints."""

from app.models.user import User
from app.core.dependencies import get_current_user_id, get_current_admin_user, get_admin_user_id
from fastapi import APIRouter, Depends, Request
from app.core.region_manager import region_manager

router = APIRouter(prefix="/infrastructure", tags=["infrastructure"])


@router.get("/regions")
async def get_regions_status():
    """Get status of all regions."""
    return {
        "regions": region_manager.get_region_status(),
        "primary_region": region_manager.primary_region,
    }


@router.get("/regions/optimal")
async def get_optimal_region(request: Request, country: str = None):
    """Get optimal region for user."""
    # Extract country from headers if not provided
    if not country:
        country = request.headers.get("CF - IPCountry", "US")

    optimal = await region_manager.get_optimal_region(country)
    return {
        "optimal_region": optimal,
        "endpoint": region_manager.regions[optimal].endpoint,
        "user_country": country,
    }


@router.post("/regions/health - check")
async def perform_health_check(admin_user: User = Depends(get_current_admin_user)):
    """Perform health check on all regions (admin only)."""
    results = await region_manager.health_check_regions()
    return {"health_check_results": results, "timestamp": "2024 - 01-01T00:00:00Z"}


@router.get("/cdn/config")
async def get_cdn_configuration():
    """Get CDN configuration."""
    return cdn_service.get_cdn_config()


@router.get("/cdn/asset - url")
async def get_asset_url(asset_path: str, region: str = None):
    """Get optimized CDN URL for asset."""
    url = cdn_service.get_asset_url(asset_path, region)
    return {"asset_url": url}
