"""Pricing endpoints for TextVerified services."""
from app.core.logging import get_logger
from fastapi import APIRouter, HTTPException
from app.services.textverified_api import get_textverified_client

logger = get_logger(__name__)
router = APIRouter(prefix="/api/verify", tags=["pricing"])


@router.get("/pricing")
async def get_pricing_list():
    """Get pricing for popular services without creating verification."""
    try:
        client = get_textverified_client()
        services = ["telegram", "whatsapp", "discord", "instagram", "tiktok", "twitter", "facebook", "gmail"]
        pricing = {}

        for service in services:
            try:
                price_data = await client.get_pricing(service, "verification")
                pricing[service] = price_data.get("cost", 0)
            except BaseException:
                pricing[service] = None

        return {
            "success": True,
            "pricing": pricing,
        }
    except Exception as e:
        logger.error(f"Get pricing error: {e}")
        raise HTTPException(status_code=500, detail="Failed to get pricing")
