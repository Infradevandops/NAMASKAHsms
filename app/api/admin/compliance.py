"""SOC 2 compliance API endpoints."""

from app.models.user import User
from app.core.dependencies import get_current_user_id, get_current_admin_user, get_admin_user_id
from fastapi import APIRouter, Depends
from app.services.compliance_service import compliance_service

router = APIRouter(prefix="/compliance", tags=["compliance"])


@router.get("/soc2/status")
async def get_soc2_status():
    """Get SOC 2 compliance status."""
    return await compliance_service.assess_compliance()


@router.get("/soc2/report")
async def generate_soc2_report(admin_user: User = Depends(get_current_admin_user)):
    """Generate SOC 2 audit report (admin only)."""
    return await compliance_service.generate_audit_report()
