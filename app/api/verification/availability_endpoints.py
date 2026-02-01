"""Availability API endpoints for real-time success rate indicators."""


from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.services.availability_service import AvailabilityService

router = APIRouter(prefix="/availability", tags=["Availability"])


@router.get("/service/{service}")
async def get_service_availability(
    service: str,
    country: str = Query(None),
    hours: int = Query(24, ge=1, le=168),
    db: Session = Depends(get_db),
):
    """Get availability stats for a service.

    Returns success rate, delivery time, and status indicator.
    """
    availability_service = AvailabilityService(db)
    return availability_service.get_service_availability(service, country, hours)


@router.get("/country/{country}")
async def get_country_availability(
    country: str,
    hours: int = Query(24, ge=1, le=168),
    db: Session = Depends(get_db),
):
    """Get availability stats for a country."""
    availability_service = AvailabilityService(db)
    return availability_service.get_country_availability(country, hours)


@router.get("/carrier/{carrier}")
async def get_carrier_availability(
    carrier: str,
    country: str = Query(None),
    hours: int = Query(24, ge=1, le=168),
    db: Session = Depends(get_db),
):
    """Get availability stats for a carrier."""
    availability_service = AvailabilityService(db)
    return availability_service.get_carrier_availability(carrier, country, hours)


@router.get("/top-services")
async def get_top_services(
    country: str = Query(None),
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db),
):
    """Get top performing services by success rate."""
    availability_service = AvailabilityService(db)
    return availability_service.get_top_services(country, limit)


@router.get("/summary")
async def get_availability_summary(
    service: str = Query(...),
    country: str = Query(...),
    carrier: str = Query(None),
    db: Session = Depends(get_db),
):
    """Get comprehensive availability summary for UI display.

    Returns combined stats with recommendation.
    """
    availability_service = AvailabilityService(db)
    return availability_service.get_availability_summary(service, country, carrier)