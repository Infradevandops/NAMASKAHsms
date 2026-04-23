"""Admin pricing control endpoints for managing provider prices and templates."""

from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user_id
from app.models.user import User
from app.services.provider_price_service import ProviderPriceService
from app.services.pricing_template_service import PricingTemplateService
from app.services.price_history_service import PriceHistoryService

router = APIRouter()


async def require_admin(
    user_id: str = Depends(get_current_user_id), db: Session = Depends(get_db)
):
    """Verify admin access."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user or not user.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")
    return user_id


@router.get("/pricing/providers/live")
async def get_live_provider_prices(
    force_refresh: bool = Query(False),
    admin_id: str = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Fetch live prices from providers with platform markup."""
    service = ProviderPriceService(db)
    return await service.get_live_prices(force_refresh=force_refresh)


@router.get("/pricing/templates")
async def list_pricing_templates(
    region: Optional[str] = Query(None),
    admin_id: str = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """List all pricing templates."""
    service = PricingTemplateService(db)
    templates = service.list_templates(region=region)
    return {"templates": [t.to_dict() for t in templates]}


@router.post("/pricing/templates")
async def create_pricing_template(
    data: Dict[str, Any],
    admin_id: str = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Create a new pricing template."""
    service = PricingTemplateService(db)
    try:
        # Extract tiers from data if present, otherwise empty list
        tiers = data.pop("tiers", [])
        name = data.pop("name")
        description = data.pop("description", "")
        region = data.pop("region", "US")
        currency = data.pop("currency", "USD")
        
        template = service.create_template(
            name=name,
            description=description,
            region=region,
            currency=currency,
            tiers=tiers,
            admin_user_id=admin_id,
            **data
        )
        return {"status": "success", "template": template.to_dict()}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/pricing/templates/{template_id}")
async def update_pricing_template(
    template_id: int,
    updates: Dict[str, Any],
    admin_id: str = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Update an existing pricing template."""
    service = PricingTemplateService(db)
    try:
        template = service.update_template(template_id, admin_id, **updates)
        return {"status": "success", "template": template.to_dict()}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/pricing/templates/{template_id}/activate")
async def activate_pricing_template(
    template_id: int,
    notes: Optional[str] = Query(None),
    admin_id: str = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Activate a pricing template."""
    service = PricingTemplateService(db)
    try:
        template = service.activate_template(template_id, admin_id, notes=notes)
        return {"status": "success", "template": template.to_dict()}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/pricing/history/{service_id}")
async def get_service_price_history(
    service_id: str,
    days: int = Query(30),
    admin_id: str = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Get historical pricing snapshots for a service."""
    service = PriceHistoryService(db)
    history = service.get_price_history(service_id, days=days)
    return {"service_id": service_id, "history": history}


@router.get("/pricing/alerts")
async def get_recent_price_alerts(
    limit: int = Query(10),
    admin_id: str = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Fetch recent price-related admin notifications."""
    service = PriceHistoryService(db)
    alerts = service.get_recent_alerts(limit=limit)
    return {"alerts": alerts}


@router.get("/pricing/balance")
async def get_provider_balance(
    admin_id: str = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Fetch live balance from TextVerified."""
    from app.services.textverified_service import TextVerifiedService
    tv = TextVerifiedService()
    return await tv.get_balance()


@router.delete("/pricing/templates/{template_id}")
async def delete_pricing_template(
    template_id: int,
    admin_id: str = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Delete an inactive pricing template with no assigned users."""
    service = PricingTemplateService(db)
    try:
        service.delete_template(template_id, admin_id)
        return {"status": "success", "message": f"Template {template_id} deleted"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/pricing/rollback")
async def rollback_pricing(
    region: str = Query("US"),
    admin_id: str = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Rollback to the previously active pricing template."""
    service = PricingTemplateService(db)
    try:
        template = service.rollback_to_previous(admin_id, region=region)
        return {"status": "success", "template": template.to_dict()}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/pricing/templates/{template_id}/clone")
async def clone_pricing_template(
    template_id: int,
    data: Dict[str, Any],
    admin_id: str = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Clone an existing pricing template with a new name."""
    new_name = data.get("name")
    if not new_name:
        raise HTTPException(status_code=400, detail="'name' is required")
    service = PricingTemplateService(db)
    try:
        template = service.clone_template(template_id, new_name, admin_id)
        return {"status": "success", "template": template.to_dict()}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
