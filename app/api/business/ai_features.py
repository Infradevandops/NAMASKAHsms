"""AI features API endpoints."""
from fastapi import APIRouter, Depends, HTTPException
from app.core.dependencies import get_current_user

router = APIRouter(prefix="/ai", tags=["ai"])


@router.get("/routing/recommend")
async def get_routing_recommendation(
    service: str,
    country: str = "0",
    current_user: User = Depends(get_current_user)
):
    """Get AI - recommended provider for service."""
    try:
        provider = await smart_router.select_provider(service, country)
        return {
            "recommended_provider": provider,
            "service": service,
            "country": country
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/fraud/analyze")
async def analyze_fraud_risk(
    service: str,
    ip_address: str = "127.0.0.1",
    current_user: User = Depends(get_current_user)
):
    """Analyze fraud risk for verification request."""
    try:
        analysis = await fraud_detector.analyze_request(
            current_user.id, service, ip_address
        )
        return analysis
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
