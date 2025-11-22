"""Rental API endpoints."""
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.core.exceptions import (InsufficientCreditsError, RentalExpiredError,
                                 RentalNotFoundError)
from app.models.user import User
from app.schemas.rental import (RentalCreate, RentalExtend,
                                RentalMessagesResponse, RentalResponse)
from app.services.rental_service import RentalService

router = APIRouter(prefix="/rentals", tags=["Rentals"])


@router.post("/create", response_model=RentalResponse)
async def create_rental(
    rental_data: RentalCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a new SMS number rental."""
    try:
        service = RentalService(db)
        return await service.create_rental(current_user.id, rental_data)
    except InsufficientCreditsError as e:
        raise HTTPException(status_code=402, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to create rental: {str(e)}"
        )


@router.get("/active", response_model=List[RentalResponse])
async def get_active_rentals(
    current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
):
    """Get user's active rentals."""
    try:
        service = RentalService(db)
        return await service.get_active_rentals(current_user.id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get rentals: {str(e)}")


@router.post("/{rental_id}/extend")
async def extend_rental(
    rental_id: str,
    extend_data: RentalExtend,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Extend rental duration."""
    try:
        service = RentalService(db)
        return await service.extend_rental(rental_id, current_user.id, extend_data)
    except RentalNotFoundError:
        raise HTTPException(status_code=404, detail="Rental not found")
    except RentalExpiredError:
        raise HTTPException(status_code=410, detail="Cannot extend expired rental")
    except InsufficientCreditsError as e:
        raise HTTPException(status_code=402, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to extend rental: {str(e)}"
        )


@router.post("/{rental_id}/release")
async def release_rental(
    rental_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Release rental early with partial refund."""
    try:
        service = RentalService(db)
        return await service.release_rental(rental_id, current_user.id)
    except RentalNotFoundError:
        raise HTTPException(status_code=404, detail="Rental not found")
    except RentalExpiredError:
        raise HTTPException(status_code=410, detail="Rental already expired")
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to release rental: {str(e)}"
        )


@router.get("/{rental_id}/messages", response_model=RentalMessagesResponse)
async def get_rental_messages(
    rental_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get SMS messages for rental."""
    try:
        service = RentalService(db)
        return await service.get_rental_messages(rental_id, current_user.id)
    except RentalNotFoundError:
        raise HTTPException(status_code=404, detail="Rental not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get messages: {str(e)}")
