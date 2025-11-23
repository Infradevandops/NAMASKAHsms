"""Wake request endpoints for dormant rental activation."""
from app.core.logging import get_logger
from app.core.dependencies import get_current_user_id
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.core.database import get_db

logger = get_logger(__name__)
router = APIRouter(prefix="/api/wake-requests", tags=["wake-requests"])
client = get_textverified_client()


@router.post("/create")
async def create_wake_request(
    request: Request,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Create wake request for dormant rental."""
    try:
        data = await request.json()
        rental_id = data.get("rental_id")

        rental = db.query(Rental).filter(
            Rental.id == rental_id, Rental.user_id == user_id
        ).first()

        if not rental:
            raise HTTPException(status_code=404, detail="Rental not found")

        # Call TextVerified API to create wake request
        headers = await client.auth_service.get_headers()
        import httpx

        async with httpx.AsyncClient() as http_client:
            response = await http_client.post(
                f"{client.BASE_URL}/api/pub/v2/wake-requests",
                headers=headers,
                json={"reservationId": rental.external_id},
                timeout=10.0,
            )
            response.raise_for_status()
            wake_data = response.json()

            return {
                "success": True,
                "wake_request_id": wake_data.get("id"),
                "rental_id": rental_id,
                "status": "active",
                "usage_window": {
                    "start": wake_data.get("usageWindowStart"),
                    "end": wake_data.get("usageWindowEnd"),
                },
            }

    except HTTPException:
        pass
    except Exception as e:
        logger.error(f"Create wake request error: {e}")
        raise HTTPException(status_code=500, detail="Failed to create wake request")


@router.post("/estimate")
async def estimate_wake_window(
    request: Request,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Estimate usage window for wake request."""
    try:
        data = await request.json()
        rental_id = data.get("rental_id")

        rental = db.query(Rental).filter(
            Rental.id == rental_id, Rental.user_id == user_id
        ).first()

        if not rental:
            raise HTTPException(status_code=404, detail="Rental not found")

        headers = await client.auth_service.get_headers()

        async with httpx.AsyncClient() as http_client:
            response = await http_client.post(
                f"{client.BASE_URL}/api/pub/v2/wake-requests/estimate",
                headers=headers,
                json={"reservationId": rental.external_id},
                timeout=10.0,
            )
            response.raise_for_status()
            estimate_data = response.json()

            return {
                "success": True,
                "estimated_window": {
                    "start": estimate_data.get("estimatedStart"),
                    "end": estimate_data.get("estimatedEnd"),
                    "duration_minutes": estimate_data.get("durationMinutes"),
                },
            }

    except HTTPException:
        pass
    except Exception as e:
        logger.error(f"Estimate wake window error: {e}")
        raise HTTPException(status_code=500, detail="Failed to estimate wake window")


@router.get("/{wake_request_id}/status")
async def get_wake_request_status(
    wake_request_id: str,
    user_id: str = Depends(get_current_user_id),
):
    """Get wake request status."""
    try:
        headers = await client.auth_service.get_headers()

        async with httpx.AsyncClient() as http_client:
            response = await http_client.get(
                f"{client.BASE_URL}/api/pub/v2/wake-requests/{wake_request_id}",
                headers=headers,
                timeout=10.0,
            )
            response.raise_for_status()
            wake_data = response.json()

            return {
                "success": True,
                "id": wake_data.get("id"),
                "status": wake_data.get("status"),
                "usage_window": {
                    "start": wake_data.get("usageWindowStart"),
                    "end": wake_data.get("usageWindowEnd"),
                },
            }

    except Exception as e:
        logger.error(f"Get wake request status error: {e}")
        raise HTTPException(status_code=500, detail="Failed to get wake request status")
