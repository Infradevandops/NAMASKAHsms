"""Enhanced white - label API endpoints."""
from app.models.user import User
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from app.core.dependencies import get_db, get_current_user
from pydantic import BaseModel
from typing import Dict, Optional

router = APIRouter(prefix="/whitelabel/v2", tags=["whitelabel_enhanced"])


class WhiteLabelSetup(BaseModel):
    domain: str
    company_name: str
    logo_url: Optional[str] = None
    primary_color: str = "#667eea"
    secondary_color: str = "#10b981"
    font_family: str = "Inter, sans - serif"
    custom_css: Optional[str] = None
    api_subdomain: Optional[str] = None
    features: Dict = {}


class BrandingUpdate(BaseModel):
    company_name: Optional[str] = None
    logo_url: Optional[str] = None
    primary_color: Optional[str] = None
    secondary_color: Optional[str] = None
    font_family: Optional[str] = None
    custom_css: Optional[str] = None


@router.post("/setup")
async def setup_whitelabel(
    setup_data: WhiteLabelSetup,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Complete white - label setup wizard."""

    if not current_user.is_affiliate:
        raise HTTPException(status_code=403, detail="Affiliate access required")

    service = get_whitelabel_enhanced_service(db)

    try:
        result = await service.setup_complete_whitelabel(
            partner_id=current_user.id,
            domain=setup_data.domain,
            company_name=setup_data.company_name,
            branding_config=setup_data.dict()
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/branding/{config_id}")
async def update_branding(
    config_id: int,
    branding_data: BrandingUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update complete branding configuration."""

    if not current_user.is_affiliate:
        raise HTTPException(status_code=403, detail="Affiliate access required")

    service = get_whitelabel_enhanced_service(db)

    try:
        result = await service.update_branding(
            config_id=config_id,
            branding_data=branding_data.dict(exclude_unset=True)
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/preview/{config_id}")
async def preview_whitelabel(
    config_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Live preview of white - label configuration."""

    service = get_whitelabel_enhanced_service(db)

    # Get configuration by ID (for preview)
    config = db.query(WhiteLabelConfig).filter(
        WhiteLabelConfig.id == config_id
    ).first()

    if not config:
        raise HTTPException(status_code=404, detail="Configuration not found")

    # Generate preview data
    preview_config = await service.get_partner_config(config.domain)

    return {
        "preview": True,
        "config": preview_config,
        "preview_url": f"https://{config.domain}",
        "css": await service.generate_custom_css(config_id)
    }


@router.post("/domain/verify")
async def verify_domain(
    domain: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Verify domain ownership."""

    if not current_user.is_affiliate:
        raise HTTPException(status_code=403, detail="Affiliate access required")

    service = get_whitelabel_enhanced_service(db)

    try:
        result = await service.verify_domain(domain)
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/analytics/{domain}")
async def get_whitelabel_analytics(
    domain: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get white - label usage analytics."""

    if not current_user.is_affiliate:
        raise HTTPException(status_code=403, detail="Affiliate access required")

    # Mock analytics data (implement actual analytics)
    return {
        "domain": domain,
        "total_users": 150,
        "monthly_active_users": 89,
        "total_verifications": 1250,
        "monthly_verifications": 340,
        "revenue_generated": 2500.00,
        "conversion_rate": 0.68,
        "top_services": [
            {"name": "WhatsApp", "count": 450},
            {"name": "Telegram", "count": 320},
            {"name": "Instagram", "count": 280}
        ]
    }


@router.get("/css/{config_id}")
async def get_custom_css(
    config_id: int,
    db: Session = Depends(get_db)
):
    """Get generated custom CSS for partner."""

    service = get_whitelabel_enhanced_service(db)
    css_content = await service.generate_custom_css(config_id)

    return Response(
        content=css_content,
        media_type="text/css",
        headers={"Cache - Control": "public, max - age = 3600"}
    )


@router.get("/manifest/{config_id}")
async def get_pwa_manifest(
    config_id: int,
    db: Session = Depends(get_db)
):
    """Get PWA manifest for partner."""

    service = get_whitelabel_enhanced_service(db)
    manifest = await service.create_pwa_manifest(config_id)

    return Response(
        content=str(manifest).replace("'", '"'),
        media_type="application/json",
        headers={"Cache - Control": "public, max - age = 86400"}
    )


@router.get("/config/{domain}")
async def get_domain_config(
    domain: str,
    db: Session = Depends(get_db)
):
    """Get white - label configuration by domain (public endpoint)."""

    service = get_whitelabel_enhanced_service(db)
    config = await service.get_partner_config(domain)

    if not config:
        return {"is_whitelabel": False}

    return {
        "is_whitelabel": True,
        "config": config
    }

# Template endpoints for white - label themes


@router.get("/templates")
async def get_available_templates():
    """Get available white - label templates."""

    return {
        "templates": [
            {
                "id": "modern",
                "name": "Modern Business",
                "preview": "/static/templates/modern - preview.png",
                "colors": ["#667eea", "#10b981", "#f59e0b"],
                "features": ["responsive", "dark_mode", "animations"]
            },
            {
                "id": "minimal",
                "name": "Minimal Clean",
                "preview": "/static/templates/minimal - preview.png",
                "colors": ["#1f2937", "#6b7280", "#10b981"],
                "features": ["responsive", "fast_loading", "accessibility"]
            },
            {
                "id": "corporate",
                "name": "Corporate Professional",
                "preview": "/static/templates/corporate - preview.png",
                "colors": ["#1e40a", "#dc2626", "#059669"],
                "features": ["responsive", "enterprise", "security_focused"]
            }
        ]
    }


@router.post("/templates/{template_id}/apply")
async def apply_template(
    template_id: str,
    config_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Apply template to white - label configuration."""

    if not current_user.is_affiliate:
        raise HTTPException(status_code=403, detail="Affiliate access required")

    # Template configurations
    templates = {
        "modern": {
            "primary_color": "#667eea",
            "secondary_color": "#10b981",
            "font_family": "Inter, sans - seri",
            "css_variables": {
                "--border - radius": "12px",
                "--shadow": "0 8px 25px rgba(0,0,0,0.1)"
            }
        },
        "minimal": {
            "primary_color": "#1f2937",
            "secondary_color": "#10b981",
            "font_family": "system - ui, sans - seri",
            "css_variables": {
                "--border - radius": "4px",
                "--shadow": "0 2px 4px rgba(0,0,0,0.1)"
            }
        },
        "corporate": {
            "primary_color": "#1e40a",
            "secondary_color": "#059669",
            "font_family": "Georgia, serif",
            "css_variables": {
                "--border - radius": "6px",
                "--shadow": "0 4px 8px rgba(0,0,0,0.15)"
            }
        }
    }

    if template_id not in templates:
        raise HTTPException(status_code=404, detail="Template not found")

    service = get_whitelabel_enhanced_service(db)

    try:
        result = await service.update_branding(
            config_id=config_id,
            branding_data=templates[template_id]
        )
        return {"success": True, "template_applied": template_id}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
