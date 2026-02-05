"""Area Code Endpoints for Verification."""


from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.dependencies import get_current_user_id
from app.services.textverified_service import TextVerifiedService

router = APIRouter(prefix="/area-codes", tags=["Area Codes"])


@router.get("")
async def get_area_codes(
    country: str = Query(..., description="Country code (e.g., US)"),
    service: str = Query(None, description="Service name (optional)"),
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Get available area codes with real-time availability count.

    Available to all authenticated users. Selection requires PAYG+ tier.
    """
try:
        tv_service = TextVerifiedService()
        area_codes = await tv_service.get_area_codes(country, service)

        # Sort by availability
        area_codes.sort(key=lambda x: x.get("available_count", 0), reverse=True)

        return {"success": True, "area_codes": area_codes}
except Exception as e:
        raise HTTPException(500, f"Failed to fetch area codes: {str(e)}")
