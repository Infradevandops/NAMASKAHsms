"""Revenue sharing and commission APIs."""
from app.models.user import User
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from app.core.dependencies import get_db, get_current_user, get_current_admin_user
from pydantic import BaseModel
from typing import Optional
from datetime import datetime

router = APIRouter(prefix="/revenue", tags=["revenue_sharing"])


class PayoutRequestCreate(BaseModel):
    amount: float
    payment_method: str
    payment_details: dict


class CommissionStats(BaseModel):
    total_earnings: float
    pending_earnings: float
    this_month: float
    commission_rate: float
    tier: str


@router.get("/dashboard", response_model=CommissionStats)
async def get_affiliate_dashboard(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get affiliate dashboard statistics."""
    if not current_user.is_affiliate:
        raise HTTPException(status_code=403, detail="Not an affiliate")

    engine = get_commission_engine(db)

    # Get earnings statistics
    total_earnings = current_user.referral_earnings or 0.0

    # Get pending earnings
    pending_result = db.query(
        db.func.sum(RevenueShare.commission_amount)
    ).filter(
        RevenueShare.partner_id == current_user.id,
        RevenueShare.status == "pending"
    ).scalar()
    pending_earnings = pending_result or 0.0

    # Get this month's earnings
    monthly_volume = await engine._get_monthly_volume(current_user.id)

    # Get current tier
    tier_info = await engine._get_partner_tier(current_user.id)

    return CommissionStats(
        total_earnings=total_earnings,
        pending_earnings=pending_earnings,
        this_month=monthly_volume,
        commission_rate=tier_info.get("base_rate", 0.0),
        tier=tier_info.get("name", "starter")
    )


@router.get("/tiers")
async def get_commission_tiers(db: Session = Depends(get_db)):
    """Get available commission tiers."""
    tiers = db.query(CommissionTier).filter(
        CommissionTier.is_active
    ).order_by(CommissionTier.min_volume.asc()).all()

    return [
        {
            "name": tier.name,
            "base_rate": tier.base_rate,
            "bonus_rate": tier.bonus_rate,
            "min_volume": tier.min_volume,
            "min_referrals": tier.min_referrals,
            "benefits": tier.benefits
        }
        for tier in tiers
    ]


@router.post("/payout/request")
async def request_payout(
    payout_data: PayoutRequestCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Request commission payout."""
    if not current_user.is_affiliate:
        raise HTTPException(status_code=403, detail="Not an affiliate")

    # Check minimum payout amount
    min_payout = 50.0  # Minimum N50
    if payout_data.amount < min_payout:
        raise HTTPException(
            status_code=400,
            detail=f"Minimum payout amount is N{min_payout}"
        )

    # Check available balance
    if payout_data.amount > current_user.referral_earnings:
        raise HTTPException(
            status_code=400,
            detail="Insufficient balance"
        )

    # Create payout request
    payout_request = PayoutRequest(
        affiliate_id=current_user.id,
        amount=payout_data.amount,
        payment_method=payout_data.payment_method,
        payment_details=payout_data.payment_details,
        status="pending"
    )

    db.add(payout_request)
    db.commit()

    return {
        "success": True,
        "message": "Payout request submitted successfully",
        "request_id": payout_request.id
    }


@router.get("/payouts")
async def get_payout_history(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get payout request history."""
    if not current_user.is_affiliate:
        raise HTTPException(status_code=403, detail="Not an affiliate")

    payouts = db.query(PayoutRequest).filter(
        PayoutRequest.affiliate_id == current_user.id
    ).order_by(PayoutRequest.created_at.desc()).all()

    return [
        {
            "id": payout.id,
            "amount": payout.amount,
            "currency": payout.currency,
            "payment_method": payout.payment_method,
            "status": payout.status,
            "created_at": payout.created_at,
            "processed_at": payout.processed_at
        }
        for payout in payouts
    ]


@router.get("/commissions")
async def get_commission_history(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get commission earning history."""
    if not current_user.is_affiliate:
        raise HTTPException(status_code=403, detail="Not an affiliate")

    commissions = db.query(RevenueShare).filter(
        RevenueShare.partner_id == current_user.id
    ).order_by(RevenueShare.created_at.desc()).limit(50).all()

    return [
        {
            "id": commission.id,
            "transaction_id": commission.transaction_id,
            "revenue_amount": commission.revenue_amount,
            "commission_rate": commission.commission_rate,
            "commission_amount": commission.commission_amount,
            "tier_name": commission.tier_name,
            "status": commission.status,
            "created_at": commission.created_at
        }
        for commission in commissions
    ]

# Admin endpoints


@router.get("/admin/payouts")
async def get_all_payout_requests(
    admin_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Get all payout requests (admin only)."""
    payouts = db.query(PayoutRequest).order_by(
        PayoutRequest.created_at.desc()
    ).all()

    return [
        {
            "id": payout.id,
            "affiliate_email": payout.affiliate.email,
            "amount": payout.amount,
            "payment_method": payout.payment_method,
            "status": payout.status,
            "created_at": payout.created_at,
            "admin_notes": payout.admin_notes
        }
        for payout in payouts
    ]


@router.put("/admin/payouts/{payout_id}/process")
async def process_payout(
    payout_id: int,
    status: str,
    admin_notes: Optional[str] = None,
    admin_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Process payout request (admin only)."""
    payout = db.query(PayoutRequest).filter(
        PayoutRequest.id == payout_id
    ).first()

    if not payout:
        raise HTTPException(status_code=404, detail="Payout request not found")

    payout.status = status
    payout.admin_notes = admin_notes
    payout.processed_at = datetime.utcnow()

    # If approved, deduct from affiliate balance
    if status == "approved":
        affiliate = payout.affiliate
        affiliate.referral_earnings -= payout.amount

    db.commit()

    return {"success": True, "status": status}
