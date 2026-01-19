from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.admin.dependencies import require_admin
from app.core.database import get_db
from app.models.pricing_template import PricingHistory, PricingTemplate, TierPricing
from app.models.user import User

router = APIRouter(prefix="/admin/pricing", tags=["admin-pricing"])


class TemplateCreate(BaseModel):
    name: str
    description: Optional[str] = None
    region: str = "US"
    currency: str = "USD"
    effective_date: Optional[datetime] = None
    expires_at: Optional[datetime] = None


class TierCreate(BaseModel):
    tier_name: str
    monthly_price: float
    included_quota: float
    overage_rate: float
    features: List[str]
    api_keys_limit: int
    display_order: int


@router.get("/templates")
async def get_pricing_templates(
    admin_user: User = Depends(require_admin), db: Session = Depends(get_db)
):
    """Get all pricing templates with their tiers"""
    templates = db.query(PricingTemplate).all()

    result = []
    for template in templates:
        tiers = (
            db.query(TierPricing).filter(TierPricing.template_id == template.id).all()
        )
        result.append(
            {
                "id": template.id,
                "name": template.name,
                "description": template.description,
                "is_active": template.is_active,
                "region": template.region,
                "currency": template.currency,
                "created_at": (
                    template.created_at.isoformat() if template.created_at else None
                ),
                "effective_date": (
                    template.effective_date.isoformat()
                    if template.effective_date
                    else None
                ),
                "expires_at": (
                    template.expires_at.isoformat() if template.expires_at else None
                ),
                "tiers": [
                    {
                        "id": tier.id,
                        "tier_name": tier.tier_name,
                        "monthly_price": float(tier.monthly_price or 0),
                        "included_quota": float(tier.included_quota or 0),
                        "overage_rate": float(tier.overage_rate or 0),
                        "features": tier.features or [],
                        "api_keys_limit": tier.api_keys_limit,
                        "display_order": tier.display_order,
                    }
                    for tier in sorted(tiers, key=lambda x: x.display_order or 0)
                ],
            }
        )

    return {"success": True, "templates": result, "total": len(result)}


@router.post("/templates")
async def create_pricing_template(
    template_data: TemplateCreate,
    tiers: List[TierCreate],
    admin_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Create new pricing template with tiers"""

    # Check if template name already exists
    existing = (
        db.query(PricingTemplate)
        .filter(PricingTemplate.name == template_data.name)
        .first()
    )
    if existing:
        raise HTTPException(status_code=400, detail="Template name already exists")

    # Create template
    template = PricingTemplate(
        name=template_data.name,
        description=template_data.description,
        region=template_data.region,
        currency=template_data.currency,
        created_by=admin_user.id,
        effective_date=template_data.effective_date,
        expires_at=template_data.expires_at,
        is_active=False,  # New templates start inactive
    )
    db.add(template)
    db.flush()  # Get the ID

    # Create tiers
    for tier_data in tiers:
        tier = TierPricing(
            template_id=template.id,
            tier_name=tier_data.tier_name,
            monthly_price=tier_data.monthly_price,
            included_quota=tier_data.included_quota,
            overage_rate=tier_data.overage_rate,
            features=tier_data.features,
            api_keys_limit=tier_data.api_keys_limit,
            display_order=tier_data.display_order,
        )
        db.add(tier)

    # Log creation
    history = PricingHistory(
        template_id=template.id,
        action="created",
        changed_by=admin_user.id,
        notes=f"Template '{template.name}' created with {len(tiers)} tiers",
    )
    db.add(history)

    db.commit()

    return {
        "success": True,
        "template_id": template.id,
        "message": "Template created successfully",
    }


@router.post("/templates/{template_id}/activate")
async def activate_template(
    template_id: int,
    admin_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Activate a pricing template (deactivates others)"""

    template = (
        db.query(PricingTemplate).filter(PricingTemplate.id == template_id).first()
    )
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")

    # Deactivate all other templates
    db.query(PricingTemplate).update({"is_active": False})

    # Activate selected template
    template.is_active = True

    # Log activation
    history = PricingHistory(
        template_id=template.id,
        action="activated",
        changed_by=admin_user.id,
        notes=f"Template '{template.name}' activated",
    )
    db.add(history)

    db.commit()

    return {"success": True, "message": f"Template '{template.name}' activated"}


@router.post("/templates/{template_id}/deactivate")
async def deactivate_template(
    template_id: int,
    admin_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Deactivate a pricing template"""

    template = (
        db.query(PricingTemplate).filter(PricingTemplate.id == template_id).first()
    )
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")

    template.is_active = False

    # Log deactivation
    history = PricingHistory(
        template_id=template.id,
        action="deactivated",
        changed_by=admin_user.id,
        notes=f"Template '{template.name}' deactivated",
    )
    db.add(history)

    db.commit()

    return {"success": True, "message": f"Template '{template.name}' deactivated"}


@router.get("/templates/active")
async def get_active_template(db: Session = Depends(get_db)):
    """Get currently active pricing template"""

    template = (
        db.query(PricingTemplate).filter(PricingTemplate.is_active ).first()
    )
    if not template:
        return {"active_template": None}

    tiers = db.query(TierPricing).filter(TierPricing.template_id == template.id).all()

    return {
        "active_template": {
            "id": template.id,
            "name": template.name,
            "description": template.description,
            "region": template.region,
            "currency": template.currency,
            "tiers": [
                {
                    "tier_name": tier.tier_name,
                    "monthly_price": float(tier.monthly_price or 0),
                    "included_quota": float(tier.included_quota or 0),
                    "overage_rate": float(tier.overage_rate or 0),
                    "features": tier.features or [],
                    "api_keys_limit": tier.api_keys_limit,
                }
                for tier in sorted(tiers, key=lambda x: x.display_order or 0)
            ],
        }
    }


@router.get("/templates/{template_id}/history")
async def get_template_history(
    template_id: int,
    admin_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Get pricing template change history"""

    history = (
        db.query(PricingHistory)
        .filter(PricingHistory.template_id == template_id)
        .order_by(PricingHistory.changed_at.desc())
        .all()
    )

    return {
        "history": [
            {
                "action": h.action,
                "changed_by": h.user.email if h.user else "System",
                "changed_at": h.changed_at.isoformat() if h.changed_at else None,
                "notes": h.notes,
            }
            for h in history
        ]
    }


@router.post("/quick-templates")
async def create_quick_templates(
    admin_user: User = Depends(require_admin), db: Session = Depends(get_db)
):
    """Create standard, promotional, and holiday templates"""

    templates_data = [
        {
            "name": "Standard Pricing",
            "description": "Regular pricing for normal operations",
            "tiers": [
                {
                    "tier_name": "Freemium",
                    "monthly_price": 0,
                    "included_quota": 0,
                    "overage_rate": 2.50,
                    "features": ["Random US numbers", "100/day"],
                    "api_keys_limit": 0,
                    "display_order": 1,
                },
                {
                    "tier_name": "Starter",
                    "monthly_price": 8.99,
                    "included_quota": 10,
                    "overage_rate": 0.50,
                    "features": ["Area code filtering", "1,000/day"],
                    "api_keys_limit": 5,
                    "display_order": 2,
                },
                {
                    "tier_name": "Pro",
                    "monthly_price": 25.00,
                    "included_quota": 30,
                    "overage_rate": 0.30,
                    "features": ["Area + ISP filtering", "10,000/day"],
                    "api_keys_limit": 10,
                    "display_order": 3,
                },
                {
                    "tier_name": "Custom",
                    "monthly_price": 35.00,
                    "included_quota": 50,
                    "overage_rate": 0.20,
                    "features": ["All features", "Unlimited"],
                    "api_keys_limit": -1,
                    "display_order": 4,
                },
            ],
        },
        {
            "name": "Promotional 50% Off",
            "description": "Limited time promotional pricing",
            "tiers": [
                {
                    "tier_name": "Freemium",
                    "monthly_price": 0,
                    "included_quota": 0,
                    "overage_rate": 2.50,
                    "features": ["Random US numbers", "100/day"],
                    "api_keys_limit": 0,
                    "display_order": 1,
                },
                {
                    "tier_name": "Starter",
                    "monthly_price": 4.49,
                    "included_quota": 15,
                    "overage_rate": 0.40,
                    "features": ["Area code filtering", "1,500/day", "🎉 50% OFF"],
                    "api_keys_limit": 5,
                    "display_order": 2,
                },
                {
                    "tier_name": "Pro",
                    "monthly_price": 12.50,
                    "included_quota": 40,
                    "overage_rate": 0.25,
                    "features": ["Area + ISP filtering", "15,000/day", "🎉 50% OFF"],
                    "api_keys_limit": 15,
                    "display_order": 3,
                },
                {
                    "tier_name": "Custom",
                    "monthly_price": 17.50,
                    "included_quota": 70,
                    "overage_rate": 0.15,
                    "features": ["All features", "Unlimited", "🎉 50% OFF"],
                    "api_keys_limit": -1,
                    "display_order": 4,
                },
            ],
        },
        {
            "name": "Holiday Special",
            "description": "Holiday season special pricing",
            "tiers": [
                {
                    "tier_name": "Freemium",
                    "monthly_price": 0,
                    "included_quota": 5,
                    "overage_rate": 2.00,
                    "features": ["Random US numbers", "200/day", "🎄 Holiday Bonus"],
                    "api_keys_limit": 1,
                    "display_order": 1,
                },
                {
                    "tier_name": "Starter",
                    "monthly_price": 6.99,
                    "included_quota": 20,
                    "overage_rate": 0.35,
                    "features": [
                        "Area code filtering",
                        "2,000/day",
                        "🎄 Holiday Special",
                    ],
                    "api_keys_limit": 8,
                    "display_order": 2,
                },
                {
                    "tier_name": "Pro",
                    "monthly_price": 19.99,
                    "included_quota": 50,
                    "overage_rate": 0.20,
                    "features": [
                        "Area + ISP filtering",
                        "20,000/day",
                        "🎄 Holiday Special",
                    ],
                    "api_keys_limit": 20,
                    "display_order": 3,
                },
                {
                    "tier_name": "Custom",
                    "monthly_price": 29.99,
                    "included_quota": 100,
                    "overage_rate": 0.10,
                    "features": ["All features", "Unlimited", "🎄 Holiday Special"],
                    "api_keys_limit": -1,
                    "display_order": 4,
                },
            ],
        },
    ]

    created_templates = []

    for template_data in templates_data:
        # Check if template already exists
        existing = (
            db.query(PricingTemplate)
            .filter(PricingTemplate.name == template_data["name"])
            .first()
        )
        if existing:
            continue

        # Create template
        template = PricingTemplate(
            name=template_data["name"],
            description=template_data["description"],
            region="US",
            currency="USD",
            created_by=admin_user.id,
            is_active=template_data["name"]
            == "Standard Pricing",  # Activate standard by default
        )
        db.add(template)
        db.flush()

        # Create tiers
        for tier_data in template_data["tiers"]:
            tier = TierPricing(
                template_id=template.id,
                tier_name=tier_data["tier_name"],
                monthly_price=tier_data["monthly_price"],
                included_quota=tier_data["included_quota"],
                overage_rate=tier_data["overage_rate"],
                features=tier_data["features"],
                api_keys_limit=tier_data["api_keys_limit"],
                display_order=tier_data["display_order"],
            )
            db.add(tier)

        created_templates.append(template.name)

    db.commit()

    return {
        "success": True,
        "created_templates": created_templates,
        "message": f"Created {len(created_templates)} pricing templates",
    }
