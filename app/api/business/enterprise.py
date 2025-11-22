"""Enterprise SLA and account management API."""
from fastapi import APIRouter, Depends, HTTPException
from app.core.dependencies import get_current_user, get_current_admin_user
from app.services.enterprise_service import enterprise_service
from app.models.user import User
from pydantic import BaseModel

router = APIRouter(prefix="/enterprise", tags=["enterprise"])


class TierUpgrade(BaseModel):
    user_id: int
    tier_name: str
    account_manager_email: str = None


@router.get("/tier")
async def get_my_enterprise_tier(current_user: User = Depends(get_current_user)):
    """Get current user's enterprise tier."""
    tier = await enterprise_service.get_user_tier(current_user.id)
    if not tier:
        return {"is_enterprise": False}

    return {"is_enterprise": True, **tier}


@router.post("/upgrade")
async def upgrade_user_to_enterprise(
    upgrade_data: TierUpgrade,
    admin_user: User = Depends(get_current_admin_user)
):
    """Upgrade user to enterprise tier (admin only)."""
    try:
        result = await enterprise_service.upgrade_to_enterprise(
            upgrade_data.user_id,
            upgrade_data.tier_name
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/sla/check")
async def check_sla_status(
    response_time: int,
    current_user: User = Depends(get_current_user)
):
    """Check SLA compliance for current request."""
    tier = await enterprise_service.get_user_tier(current_user.id)
    if not tier:
        return {"message": "Not an enterprise user"}

    compliance = await enterprise_service.check_sla_compliance(
        response_time,
        tier["tier_name"]
    )
    return compliance
