"""Pricing information and estimation endpoints."""
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user_id
from app.core.logging import get_logger
from app.services.pricing_service import PricingService

logger = get_logger(__name__)
router = APIRouter(prefix="/api/pricing", tags=["Pricing"])


@router.get("/tiers")
async def get_pricing_tiers(db: Session = Depends(get_db)):
    """Get all pricing tiers.
    
    Returns:
        - List of pricing tiers with features and pricing
    """
    try:
        pricing_service = PricingService(db)
        tiers = pricing_service.get_all_tiers()
        
        logger.info(f"Retrieved {len(tiers)} pricing tiers")
        
        return {
            "tiers": tiers,
            "total": len(tiers)
        }
    
    except Exception as e:
        logger.error(f"Failed to get pricing tiers: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve pricing tiers"
        )


@router.get("/tier/{tier_name}")
async def get_pricing_tier(
    tier_name: str,
    db: Session = Depends(get_db)
):
    """Get specific pricing tier details.
    
    Path Parameters:
        - tier_name: Tier name (BASIC, STANDARD, PREMIUM, ENTERPRISE)
    
    Returns:
        - Tier details with features and pricing
    """
    try:
        pricing_service = PricingService(db)
        tier_features = pricing_service.get_tier_features(tier_name)
        
        logger.info(f"Retrieved tier details: {tier_name}")
        
        return tier_features
    
    except ValueError as e:
        logger.error(f"Validation error: {str(e)}")
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to get tier details: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve tier details"
        )


@router.get("/compare")
async def compare_tiers(db: Session = Depends(get_db)):
    """Get comparison of all pricing tiers.
    
    Returns:
        - List of all tiers with features for comparison
    """
    try:
        pricing_service = PricingService(db)
        comparison = pricing_service.compare_tiers()
        
        logger.info("Retrieved tier comparison")
        
        return {
            "tiers": comparison,
            "total": len(comparison)
        }
    
    except Exception as e:
        logger.error(f"Failed to compare tiers: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to compare tiers"
        )


@router.get("/addons")
async def get_addon_pricing(db: Session = Depends(get_db)):
    """Get pricing for add-on services.
    
    Returns:
        - Dictionary of available add-ons with pricing
    """
    try:
        pricing_service = PricingService(db)
        addons = pricing_service.get_addon_pricing()
        
        logger.info(f"Retrieved {len(addons)} add-on options")
        
        return {
            "addons": addons,
            "total": len(addons)
        }
    
    except Exception as e:
        logger.error(f"Failed to get add-on pricing: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve add-on pricing"
        )


@router.get("/estimate")
async def estimate_verification_cost(
    service: str = Query(..., description="Service name (telegram, whatsapp, etc)"),
    country: str = Query("US", description="Country code"),
    tier: str = Query("STANDARD", description="Pricing tier"),
    quantity: int = Query(1, ge=1, le=1000, description="Number of verifications"),
    delivery_speed: str = Query("standard", description="standard, expedited, or ultra_fast"),
    use_priority_numbers: bool = Query(False, description="Use priority numbers"),
    db: Session = Depends(get_db)
):
    """Estimate cost for verification(s).
    
    Query Parameters:
        - service: Service name (required)
        - country: Country code (default US)
        - tier: Pricing tier (default STANDARD)
        - quantity: Number of verifications (default 1)
        - delivery_speed: Delivery speed option (default standard)
        - use_priority_numbers: Whether to use priority numbers (default false)
    
    Returns:
        - Cost breakdown with all charges and discounts
    """
    try:
        pricing_service = PricingService(db)
        cost_breakdown = pricing_service.calculate_verification_cost(
            service=service,
            country=country,
            tier=tier,
            quantity=quantity,
            delivery_speed=delivery_speed,
            use_priority_numbers=use_priority_numbers,
        )
        
        logger.info(
            f"Estimated cost: Service={service}, Country={country}, "
            f"Tier={tier}, Quantity={quantity}, Total=${cost_breakdown['total_cost']}"
        )
        
        return cost_breakdown
    
    except ValueError as e:
        logger.error(f"Validation error: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to estimate cost: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to estimate cost"
        )


@router.get("/monthly-estimate")
async def estimate_monthly_cost(
    tier: str = Query("STANDARD", description="Pricing tier"),
    estimated_verifications: int = Query(100, ge=0, description="Estimated monthly verifications"),
    avg_service: str = Query("telegram", description="Average service used"),
    avg_country: str = Query("US", description="Average country"),
    use_priority_percent: float = Query(0.0, ge=0.0, le=100.0, description="Percentage using priority numbers"),
    db: Session = Depends(get_db)
):
    """Estimate monthly cost for a user.
    
    Query Parameters:
        - tier: Pricing tier (default STANDARD)
        - estimated_verifications: Estimated monthly verifications (default 100)
        - avg_service: Average service used (default telegram)
        - avg_country: Average country (default US)
        - use_priority_percent: Percentage using priority numbers (default 0)
    
    Returns:
        - Monthly cost estimate with subscription and verification costs
    """
    try:
        pricing_service = PricingService(db)
        monthly_estimate = pricing_service.estimate_monthly_cost(
            tier=tier,
            estimated_verifications_per_month=estimated_verifications,
            avg_service=avg_service,
            avg_country=avg_country,
            use_priority_numbers_percent=use_priority_percent,
        )
        
        logger.info(
            f"Estimated monthly cost: Tier={tier}, "
            f"Verifications={estimated_verifications}, "
            f"Total=${monthly_estimate['total_monthly_cost']}"
        )
        
        return monthly_estimate
    
    except ValueError as e:
        logger.error(f"Validation error: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to estimate monthly cost: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to estimate monthly cost"
        )


@router.get("/services")
async def get_available_services(db: Session = Depends(get_db)):
    """Get list of available services with base costs.
    
    Returns:
        - Dictionary of services with base costs
    """
    try:
        pricing_service = PricingService(db)
        services = {
            service: cost
            for service, cost in pricing_service.SERVICE_COSTS.items()
        }
        
        logger.info(f"Retrieved {len(services)} available services")
        
        return {
            "services": services,
            "total": len(services)
        }
    
    except Exception as e:
        logger.error(f"Failed to get services: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve services"
        )


@router.get("/countries")
async def get_available_countries(db: Session = Depends(get_db)):
    """Get list of available countries with multipliers.
    
    Returns:
        - Dictionary of countries with cost multipliers
    """
    try:
        pricing_service = PricingService(db)
        countries = {
            country: multiplier
            for country, multiplier in pricing_service.COUNTRY_MULTIPLIERS.items()
        }
        
        logger.info(f"Retrieved {len(countries)} available countries")
        
        return {
            "countries": countries,
            "total": len(countries)
        }
    
    except Exception as e:
        logger.error(f"Failed to get countries: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve countries"
        )
