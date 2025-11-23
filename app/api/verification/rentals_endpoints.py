"""Rental endpoints for TextVerified."""
from app.core.logging import get_logger
from fastapi import APIRouter, Depends, HTTPException
from app.core.dependencies import get_current_user_id

logger = get_logger(__name__)
router = APIRouter(prefix="/api/rentals", tags=["rentals"])
integration = get_textverified_integration()


@router.get("/")
async def list_rentals(user_id: str = Depends(get_current_user_id)):
    """List all active rentals."""
    try:
        renewable = await integration.get_active_rentals()
        return {
            "success": True,
            "rentals": renewable,
            "total": len(renewable),
        }
    except Exception as e:
        logger.error(f"List rentals error: {e}")
        raise HTTPException(status_code=500, detail="Failed to list rentals")


@router.post("/{rental_id}/extend")
async def extend_rental(
    rental_id: str,
    duration_days: int,
    user_id: str = Depends(get_current_user_id),
):
    """Extend rental duration."""
    try:
        result = await integration.extend_rental(rental_id, duration_days)
        return {
            "success": True,
            "rental_id": rental_id,
            "new_expiry": result.get("expires_at"),
            "cost": result.get("cost"),
        }
    except Exception as e:
        logger.error(f"Extend rental error: {e}")
        raise HTTPException(status_code=500, detail="Failed to extend rental")
