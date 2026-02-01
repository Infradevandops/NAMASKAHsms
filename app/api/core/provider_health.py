"""Provider health check endpoints."""


from fastapi import APIRouter, HTTPException
from app.core.logging import get_logger
from app.services.provider_registry import provider_manager

logger = get_logger(__name__)
router = APIRouter(prefix="/api/providers", tags=["providers"])


@router.get("/health")
async def get_provider_health():
    """Get health status of all SMS providers."""
try:
        health_status = await provider_manager.health_check_all()
if not health_status:
            raise HTTPException(status_code=503, detail="No providers configured")
        return {"status": "ok", "providers": health_status}
except Exception as e:
        logger.error(f"Error getting provider health: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health/{provider_name}")
async def get_provider_health_by_name(provider_name: str):
    """Get health status of specific provider."""
try:
if provider_name not in provider_manager.providers:
            raise HTTPException(status_code=404, detail=f"Provider {provider_name} not found")

        provider_stats = provider_manager.get_provider_stats()
        provider_info = provider_stats["providers"].get(provider_name)

if not provider_info:
            raise HTTPException(status_code=404, detail=f"Provider {provider_name} not found")

        return {"status": "ok", "provider": provider_info}
except HTTPException:
        pass
except Exception as e:
        logger.error(f"Error getting provider health: {e}")
        raise HTTPException(status_code=500, detail=str(e))