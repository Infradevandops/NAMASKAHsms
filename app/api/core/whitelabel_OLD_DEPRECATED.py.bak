"""Whitelabel configuration endpoints."""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user_id
from app.models.user import User
from app.models.whitelabel import WhiteLabelConfig

router = APIRouter(prefix="/api/whitelabel", tags=["Whitelabel"])


class WhitelabelConfigRequest(BaseModel):
    company_name: str
    domain: str
    logo_url: Optional[str] = None
    primary_color: str = "#2563eb"
    secondary_color: str = "#7c3aed"
    features: Optional[dict] = None


async def require_pro(
    user_id: str = Depends(get_current_user_id), db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if user.subscription_tier not in ("pro", "custom"):
        raise HTTPException(
            status_code=402, detail="Whitelabel requires Pro or Custom tier"
        )
    return user_id


@router.get("")
async def get_whitelabel_config(
    user_id: str = Depends(require_pro), db: Session = Depends(get_db)
):
    """Get current user's whitelabel configuration."""
    config = (
        db.query(WhiteLabelConfig)
        .filter(WhiteLabelConfig.partner_id == user_id)
        .first()
    )
    if not config:
        return {"configured": False}
    return {
        "configured": True,
        "company_name": config.company_name,
        "domain": config.domain,
        "logo_url": config.logo_url,
        "primary_color": config.primary_color,
        "secondary_color": config.secondary_color,
        "features": config.features or {},
        "enabled": config.enabled,
    }


@router.post("")
async def save_whitelabel_config(
    payload: WhitelabelConfigRequest,
    user_id: str = Depends(require_pro),
    db: Session = Depends(get_db),
):
    """Create or update whitelabel configuration."""
    config = (
        db.query(WhiteLabelConfig)
        .filter(WhiteLabelConfig.partner_id == user_id)
        .first()
    )
    default_features = {"sms": True, "rentals": True, "analytics": False, "api": False}
    features = payload.features or default_features

    if config:
        config.company_name = payload.company_name
        config.domain = payload.domain
        config.logo_url = payload.logo_url
        config.primary_color = payload.primary_color
        config.secondary_color = payload.secondary_color
        config.features = features
    else:
        config = WhiteLabelConfig(
            partner_id=user_id,
            company_name=payload.company_name,
            domain=payload.domain,
            logo_url=payload.logo_url,
            primary_color=payload.primary_color,
            secondary_color=payload.secondary_color,
            features=features,
            enabled=True,
        )
        db.add(config)

    db.commit()
    db.refresh(config)
    return {"status": "saved", "domain": config.domain}


@router.delete("")
async def delete_whitelabel_config(
    user_id: str = Depends(require_pro), db: Session = Depends(get_db)
):
    """Delete whitelabel configuration."""
    config = (
        db.query(WhiteLabelConfig)
        .filter(WhiteLabelConfig.partner_id == user_id)
        .first()
    )
    if not config:
        raise HTTPException(status_code=404, detail="No whitelabel config found")
    db.delete(config)
    db.commit()
    return {"status": "deleted"}
