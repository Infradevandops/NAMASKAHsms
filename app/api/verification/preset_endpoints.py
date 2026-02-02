"""API endpoints for managing verification presets (Tier 3 feature)."""


from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.dependencies import get_current_user_id, require_tier
from app.core.logging import get_logger
from app.models.verification_preset import VerificationPreset
from app.services.tier_manager import TierManager

logger = get_logger(__name__)
router = APIRouter(prefix="/presets", tags=["Verification Presets"])

# Require 'pro' tier for this feature
require_pro = require_tier("pro")


class PresetCreate(BaseModel):

    name: str
    service_id: str
    country_id: str = "US"
    area_code: Optional[str] = None
    carrier: Optional[str] = None


class PresetResponse(PresetCreate):

    id: str

class Config:

        from_attributes = True


    @router.get("/", response_model=List[PresetResponse])
    async def get_presets(user_id: str = Depends(get_current_user_id), db: Session = Depends(get_db)):
        """Get all saved presets for the current user."""
    # Note: We don't strictly enforce tier on GET so even if downgraded they can see (but maybe not use/edit)
    # But for now, let's enforce PRO to verify consistency
        tier_manager = TierManager(db)
        if not tier_manager.check_feature_access(user_id, "isp_filtering"):  # Proxy for pro features
        # Or just check tier directly
        pass
        # We allow listing for now

        presets = db.query(VerificationPreset).filter(VerificationPreset.user_id == user_id).all()
        return presets


        @router.post("/", response_model=PresetResponse)
    async def create_preset(
        preset_data: PresetCreate,
        user_id: str = Depends(require_pro),  # Enforce PRO tier
        db: Session = Depends(get_db),
        ):
        """Create a new verification preset."""

    # Check limit (e.g. 10 presets)
        count = db.query(VerificationPreset).filter(VerificationPreset.user_id == user_id).count()
        if count >= 10:
        raise HTTPException(status_code=400, detail="Maximum of 10 presets allowed")

        preset = VerificationPreset(
        user_id=user_id,
        name=preset_data.name,
        service_id=preset_data.service_id,
        country_id=preset_data.country_id,
        area_code=preset_data.area_code,
        carrier=preset_data.carrier,
        )

        db.add(preset)
        db.commit()
        db.refresh(preset)

        logger.info(f"Created preset {preset.id} for user {user_id}")
        return preset


        @router.delete("/{preset_id}")
    async def delete_preset(
        preset_id: str,
        user_id: str = Depends(get_current_user_id),
        db: Session = Depends(get_db),
        ):
        """Delete a preset."""
        preset = (
        db.query(VerificationPreset)
        .filter(VerificationPreset.id == preset_id, VerificationPreset.user_id == user_id)
        .first()
        )

        if not preset:
        raise HTTPException(status_code=404, detail="Preset not found")

        db.delete(preset)
        db.commit()
        return {"success": True, "message": "Preset deleted"}