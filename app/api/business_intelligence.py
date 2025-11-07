"""Business intelligence API endpoints."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.services.business_intelligence import BusinessIntelligenceService

router = APIRouter(prefix="/business", tags=["Business Intelligence"])

@router.get("/revenue")
async def get_revenue_metrics(
    days: int = 30,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get revenue metrics."""
    try:
        service = BusinessIntelligenceService(db)
        return await service.get_revenue_metrics(days)
    except Exception:
        raise HTTPException(status_code=500, detail="Failed to get revenue metrics")

@router.get("/users")
async def get_user_segmentation(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get user segmentation data."""
    try:
        service = BusinessIntelligenceService(db)
        return await service.get_user_segmentation()
    except Exception:
        raise HTTPException(status_code=500, detail="Failed to get user data")

@router.get("/predictions")
async def get_predictive_analytics(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get predictive analytics."""
    try:
        service = BusinessIntelligenceService(db)
        return await service.get_predictive_analytics()
    except Exception:
        raise HTTPException(status_code=500, detail="Failed to get predictions")