"""Rental API endpoints - Updated Error Handling"""
from app.core.logging import get_logger
from app.models.user import User
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
    InsufficientCreditsError,
    RentalError,
    ResourceNotFoundError,
)
    RentalCreate,
    RentalExtend,
    RentalMessagesResponse,
    RentalResponse,
)

logger = get_logger(__name__)
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
        logger.warning(f"Insufficient credits for rental: {create_safe_error_detail(e)}")
        raise HTTPException(status_code=402, detail="Insufficient credits for this operation")
    except Exception as e:
        logger.error(f"Failed to create rental: {create_safe_error_detail(e)}")
        raise HTTPException(status_code=500, detail="Failed to create rental")


@router.get("/active", response_model=List[RentalResponse])
async def get_active_rentals(
    current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
):
    """Get user's active rentals."""
    try:
        service = RentalService(db)
        return await service.get_active_rentals(current_user.id)
    except Exception as e:
        logger.error(f"Failed to get rentals: {create_safe_error_detail(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve rentals")


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
    except ResourceNotFoundError as e:
        logger.warning(f"Rental not found: {create_safe_error_detail(e)}")
        raise HTTPException(status_code=404, detail="Rental not found")
    except RentalError as e:
        logger.warning(f"Rental error: {create_safe_error_detail(e)}")
        raise HTTPException(status_code=410, detail="Rental operation failed")
    except InsufficientCreditsError as e:
        logger.warning(f"Insufficient credits: {create_safe_error_detail(e)}")
        raise HTTPException(status_code=402, detail="Insufficient credits for this operation")
    except Exception as e:
        logger.error(f"Failed to extend rental: {create_safe_error_detail(e)}")
        raise HTTPException(status_code=500, detail="Failed to extend rental")


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
    except ResourceNotFoundError as e:
        logger.warning(f"Rental not found: {create_safe_error_detail(e)}")
        raise HTTPException(status_code=404, detail="Rental not found")
    except RentalError as e:
        logger.warning(f"Rental error: {create_safe_error_detail(e)}")
        raise HTTPException(status_code=410, detail="Rental operation failed")
    except Exception as e:
        logger.error(f"Failed to release rental: {create_safe_error_detail(e)}")
        raise HTTPException(status_code=500, detail="Failed to release rental")


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
    except ResourceNotFoundError as e:
        logger.warning(f"Rental not found: {create_safe_error_detail(e)}")
        raise HTTPException(status_code=404, detail="Rental not found")
    except Exception as e:
        logger.error(f"Failed to get messages: {create_safe_error_detail(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve messages")
