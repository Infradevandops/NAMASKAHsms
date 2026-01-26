"""Affiliate program API endpoints.

Requires payg tier or higher for access.
"""

import logging
from typing import Dict, List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import require_tier
from app.models.affiliate import AffiliateApplication
from app.services.affiliate_service import affiliate_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/affiliate", tags=["Affiliate Program"])

# Tier dependency for payg+ access
require_payg = require_tier("payg")


@router.get("/programs")
async def get_available_programs(user_id: str = Depends(require_payg), db: Session = Depends(get_db)) -> Dict:
    """Get available affiliate programs."""
    logger.info(f"Affiliate programs requested by user_id: {user_id}")
    result = await affiliate_service.get_available_programs(db)
    logger.debug(f"Retrieved {len(result.get('programs', []))} affiliate programs for user {user_id}")
    return result


@router.post("/apply")
async def apply_for_affiliate(
    application_data: Dict,
    user_id: str = Depends(require_payg),
    db: Session = Depends(get_db),
) -> Dict:
    """Apply for affiliate program."""
    logger.info(
        f"Affiliate application submitted by user_id: {user_id}, program_type: {application_data.get('program_type')}"
    )
    try:
        result = await affiliate_service.create_application(
            email=application_data.get("email"),
            program_type=application_data.get("program_type", "referral"),
            company_name=application_data.get("company_name"),
            website=application_data.get("website"),
            monthly_volume=application_data.get("monthly_volume"),
            db=db,
        )
        logger.info(f"Affiliate application created successfully for user {user_id}")
        return result
    except ValueError as e:
        logger.warning(f"Affiliate application validation failed for user {user_id}: {str(e)}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/applications")
async def get_my_applications(user_id: str = Depends(require_payg), db: Session = Depends(get_db)) -> List[Dict]:
    """Get user's affiliate applications."""
    logger.info(f"Affiliate applications requested by user_id: {user_id}")

    applications = (
        db.query(AffiliateApplication)
        .filter(AffiliateApplication.email.isnot(None))  # Placeholder - would filter by user
        .order_by(AffiliateApplication.created_at.desc())
        .limit(10)
        .all()
    )

    logger.debug(f"Retrieved {len(applications)} affiliate applications for user {user_id}")

    return [
        {
            "id": app.id,
            "program_type": app.program_type,
            "status": app.status,
            "created_at": app.created_at.isoformat() if app.created_at else None,
        }
        for app in applications
    ]


@router.get("/stats")
async def get_affiliate_stats(user_id: str = Depends(require_payg), db: Session = Depends(get_db)) -> Dict:
    """Get affiliate statistics for current user."""
    logger.debug(f"Affiliate stats requested by user_id: {user_id}")

    # Placeholder stats - would be calculated from actual data
    return {
        "total_referrals": 0,
        "pending_commission": 0.0,
        "paid_commission": 0.0,
        "referral_link": f"/ref/{user_id[:8]}",
        "conversion_rate": 0.0,
    }
