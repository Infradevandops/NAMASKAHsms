"""Rental analytics API endpoints."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.services.analytics_service import RentalAnalyticsService

router = APIRouter(prefix="/analytics/rentals", tags=["Rental Analytics"])


@router.get("/stats")
async def get_rental_stats(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get user rental statistics."""
    try:
        service = RentalAnalyticsService(db)
        return await service.get_rental_stats(current_user.id)
    except Exception:
        raise HTTPException(status_code=500, detail="Failed to get rental stats")


@router.get("/providers")
async def get_provider_performance(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get provider performance metrics."""
    try:
        service = RentalAnalyticsService(db)
        return await service.get_provider_performance()
    except Exception:
        raise HTTPException(status_code=500, detail="Failed to get provider stats")
