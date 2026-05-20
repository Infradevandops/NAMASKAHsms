"""SOC 2 compliance API endpoints."""

import logging

from fastapi import APIRouter, Depends

from app.core.dependencies import get_current_admin_user
from app.models.user import User
from app.services.compliance_service import compliance_service

logger = logging.getLogger(__name__)
from fastapi import HTTPException

router = APIRouter(prefix="/compliance", tags=["compliance"])


@router.get("/soc2/status")
async def get_soc2_status():
    try:
        """Get SOC 2 compliance status."""
        return await compliance_service.assess_compliance()
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in get_soc2_status: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/soc2/report")
async def generate_soc2_report(admin_user: User = Depends(get_current_admin_user)):
    try:
        """Generate SOC 2 audit report (admin only)."""
        return await compliance_service.generate_audit_report()
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in generate_soc2_report: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")
