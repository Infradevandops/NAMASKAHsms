"""Rental verification endpoints."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional

from app.core.database import get_db
from app.core.dependencies import get_current_user_id
from app.services.rental_service import RentalService
from app.schemas.verification import VerificationRequest

router = APIRouter(prefix="/rentals", tags=["Rentals"])

@router.post("/request", status_code=status.HTTP_201_CREATED)
async def request_rental(
    request: VerificationRequest,
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user_id)
):
    """Request a new number rental."""
    service = RentalService(db)
    try:
        # Use duration_hours if provided in the request, otherwise default to 24h
        duration = getattr(request, 'duration_hours', 24.0)
        
        result = await service.purchase_rental(
            user_id=user_id,
            service=request.service,
            country=request.country,
            duration_hours=duration
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        import logging
        logging.getLogger(__name__).error(f"Rental request failed: {e}")
        raise HTTPException(status_code=500, detail=f"Rental service temporarily unavailable: {str(e)}")

@router.get("/active")
async def get_active_rentals(
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user_id)
):
    """List all active rentals for the user."""
    service = RentalService(db)
    rentals = await service.get_active_rentals(user_id)
    return {
        "rentals": [
            {
                "id": r.id,
                "phone_number": r.phone_number,
                "service": r.service_name,
                "expires_at": r.expires_at.isoformat(),
                "status": r.status
            }
            for r in rentals
        ]
    }

@router.get("/{rental_id}/messages")
async def get_rental_messages(
    rental_id: int,
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user_id)
):
    """Fetch all messages for a specific rental (Institutional Grade)."""
    service = RentalService(db)
    messages = await service.check_rental_messages(rental_id)
    return {"messages": messages}
