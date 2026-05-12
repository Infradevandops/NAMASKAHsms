"""Admin pricing control endpoints for managing provider prices and templates."""  # noqa: E501

import logging
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user_id
from app.models.user import User
from app.services.price_history_service import PriceHistoryService
from app.services.pricing_template_service import PricingTemplateService
from app.services.provider_price_service import ProviderPriceService

logger = logging.getLogger(__name__)
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
    try:
        service = ProviderPriceService(db)
        return await service.get_live_prices(force_refresh=force_refresh)
    except Exception as e:
        logger.error(f"Failed to get live provider prices: {e}", exc_info=True)
        raise HTTPException(
            status_code=500, detail="Failed to get live provider prices"
        )


@router.get("/pricing/templates")
async def list_pricing_templates(
    region: Optional[str] = Query(None),
    admin_id: str = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """List all pricing templates."""
    try:
        service = PricingTemplateService(db)
        templates = service.list_templates(region=region)
        return {"templates": [t.to_dict() for t in templates]}
    except Exception as e:
        logger.error(f"Failed to list pricing templates: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to list pricing templates")


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
            **data,
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
        template = service.activate_template(
            template_id, admin_id, notes=notes
        )  # noqa: E501
        try:
            import asyncio

            from app.services.audit_service import AuditService

            asyncio.create_task(
                AuditService(db).log_action(
                    user_id=admin_id,
                    action="pricing_template_activated",
                    resource_type="pricing_template",
                    resource_id=str(template_id),
                    details={"template_name": template.name, "notes": notes},
                )
            )
        except Exception:
            pass
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


@router.post("/pricing/templates/promo")
async def create_promo_template(
    data: Dict[str, Any],
    admin_id: str = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Create a promotional pricing template with discount and expiry."""
    from datetime import datetime

    service = PricingTemplateService(db)
    try:
        tiers = data.pop("tiers", [])
        name = data.pop("name")
        expires_at_str = data.pop("expires_at", None)
        discount_percentage = float(data.pop("discount_percentage", 0))
        expires_at = (
            datetime.fromisoformat(expires_at_str) if expires_at_str else None
        )  # noqa: E501
        template = service.create_template(
            name=name,
            description=data.pop("description", ""),
            region=data.pop("region", "US"),
            currency=data.pop("currency", "USD"),
            tiers=tiers,
            admin_user_id=admin_id,
            is_promotional=True,
            discount_percentage=discount_percentage,
            expires_at=expires_at,
            **data,
        )
        return {"status": "success", "template": template.to_dict()}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/pricing/templates/active-promo")
async def get_active_promo_templates(
    admin_id: str = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """List all currently active promotional templates."""
    from datetime import datetime, timezone

    from app.models.pricing_template import PricingTemplate

    now = datetime.now(timezone.utc)
    promos = (
        db.query(PricingTemplate)
        .filter(
            PricingTemplate.is_promotional.is_(True),
            PricingTemplate.is_active.is_(True),
            (PricingTemplate.expires_at.is_(None))
            | (PricingTemplate.expires_at >= now),
        )
        .all()
    )
    return {"active_promos": [t.to_dict() for t in promos]}


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
        return {
            "status": "success",
            "message": f"Template {template_id} deleted",
        }  # noqa: E501
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
