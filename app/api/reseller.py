"""Reseller program API endpoints."""
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from app.core.dependencies import get_db, get_current_user, get_current_admin_user
from app.services.reseller_service import get_reseller_service
from app.models.user import User
from pydantic import BaseModel, EmailStr
from typing import List, Optional, Dict

router = APIRouter(prefix="/reseller", tags=["reseller"])

class SubAccountCreate(BaseModel):
    name: str
    email: EmailStr
    initial_credits: float = 0.0
    usage_limit: Optional[float] = None
    features: Dict = {}

class CreditAllocation(BaseModel):
    sub_account_id: int
    amount: float
    notes: Optional[str] = None

class BulkCreditTopup(BaseModel):
    account_ids: List[int]
    amount_per_account: float

@router.post("/register")
async def register_reseller(
    tier: str = "bronze",
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Register as reseller."""
    
    if not current_user.is_affiliate:
        raise HTTPException(status_code=403, detail="Must be affiliate first")
    
    service = get_reseller_service(db)
    
    try:
        result = await service.create_reseller_account(
            user_id=current_user.id,
            tier=tier
        )
        
        if result.get("error"):
            raise HTTPException(status_code=400, detail=result["error"])
        
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/accounts/create")
async def create_sub_account(
    account_data: SubAccountCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create new sub-account."""
    
    # Get reseller account
    from app.models.reseller import ResellerAccount
    reseller = db.query(ResellerAccount).filter(
        ResellerAccount.user_id == current_user.id
    ).first()
    
    if not reseller:
        raise HTTPException(status_code=403, detail="Not a reseller")
    
    service = get_reseller_service(db)
    
    try:
        result = await service.create_sub_account(
            reseller_id=reseller.id,
            name=account_data.name,
            email=account_data.email,
            initial_credits=account_data.initial_credits,
            features=account_data.features
        )
        
        if result.get("error"):
            raise HTTPException(status_code=400, detail=result["error"])
        
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/accounts")
async def get_sub_accounts(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all sub-accounts."""
    
    from app.models.reseller import ResellerAccount
    reseller = db.query(ResellerAccount).filter(
        ResellerAccount.user_id == current_user.id
    ).first()
    
    if not reseller:
        raise HTTPException(status_code=403, detail="Not a reseller")
    
    service = get_reseller_service(db)
    accounts = await service.get_sub_accounts(reseller.id)
    
    return {"sub_accounts": accounts}

@router.post("/credits/allocate")
async def allocate_credits(
    allocation: CreditAllocation,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Allocate credits to sub-account."""
    
    from app.models.reseller import ResellerAccount
    reseller = db.query(ResellerAccount).filter(
        ResellerAccount.user_id == current_user.id
    ).first()
    
    if not reseller:
        raise HTTPException(status_code=403, detail="Not a reseller")
    
    service = get_reseller_service(db)
    
    try:
        result = await service.allocate_credits(
            reseller_id=reseller.id,
            sub_account_id=allocation.sub_account_id,
            amount=allocation.amount,
            notes=allocation.notes
        )
        
        if result.get("error"):
            raise HTTPException(status_code=400, detail=result["error"])
        
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/credits/bulk-topup")
async def bulk_credit_topup(
    bulk_data: BulkCreditTopup,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Bulk credit top-up for multiple accounts."""
    
    from app.models.reseller import ResellerAccount
    reseller = db.query(ResellerAccount).filter(
        ResellerAccount.user_id == current_user.id
    ).first()
    
    if not reseller:
        raise HTTPException(status_code=403, detail="Not a reseller")
    
    service = get_reseller_service(db)
    
    try:
        result = await service.bulk_credit_topup(
            reseller_id=reseller.id,
            account_ids=bulk_data.account_ids,
            amount_per_account=bulk_data.amount_per_account
        )
        
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/usage/report")
async def get_usage_report(
    days: int = 30,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get usage analytics report."""
    
    from app.models.reseller import ResellerAccount
    reseller = db.query(ResellerAccount).filter(
        ResellerAccount.user_id == current_user.id
    ).first()
    
    if not reseller:
        raise HTTPException(status_code=403, detail="Not a reseller")
    
    service = get_reseller_service(db)
    report = await service.get_usage_report(reseller.id, days)
    
    return report

@router.put("/pricing/update")
async def update_custom_pricing(
    pricing_data: Dict,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update custom pricing for reseller."""
    
    from app.models.reseller import ResellerAccount
    reseller = db.query(ResellerAccount).filter(
        ResellerAccount.user_id == current_user.id
    ).first()
    
    if not reseller:
        raise HTTPException(status_code=403, detail="Not a reseller")
    
    # Update custom rates
    reseller.custom_rates = pricing_data
    db.commit()
    
    return {
        "success": True,
        "message": "Custom pricing updated",
        "rates": pricing_data
    }

@router.get("/dashboard")
async def get_reseller_dashboard(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get reseller dashboard data."""
    
    from app.models.reseller import ResellerAccount
    reseller = db.query(ResellerAccount).filter(
        ResellerAccount.user_id == current_user.id
    ).first()
    
    if not reseller:
        raise HTTPException(status_code=403, detail="Not a reseller")
    
    service = get_reseller_service(db)
    
    # Get basic stats
    sub_accounts = await service.get_sub_accounts(reseller.id)
    usage_report = await service.get_usage_report(reseller.id, 30)
    
    return {
        "reseller_info": {
            "tier": reseller.tier,
            "volume_discount": reseller.volume_discount,
            "credit_limit": reseller.credit_limit,
            "is_active": reseller.is_active
        },
        "sub_accounts_count": len(sub_accounts),
        "active_accounts": len([a for a in sub_accounts if a["is_active"]]),
        "total_credits_allocated": usage_report["total_credits_allocated"],
        "total_usage": usage_report["total_usage"],
        "recent_accounts": sub_accounts[:5]  # Last 5 accounts
    }

# Admin endpoints
@router.get("/admin/all")
async def get_all_resellers(
    admin_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Get all reseller accounts (admin only)."""
    
    from app.models.reseller import ResellerAccount
    resellers = db.query(ResellerAccount).join(User).all()
    
    return [
        {
            "id": reseller.id,
            "user_email": reseller.user.email,
            "tier": reseller.tier,
            "volume_discount": reseller.volume_discount,
            "is_active": reseller.is_active,
            "created_at": reseller.created_at,
            "sub_accounts_count": len(reseller.sub_accounts)
        }
        for reseller in resellers
    ]

@router.put("/admin/{reseller_id}/tier")
async def update_reseller_tier(
    reseller_id: int,
    new_tier: str,
    admin_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Update reseller tier (admin only)."""
    
    from app.models.reseller import ResellerAccount
    reseller = db.query(ResellerAccount).filter(
        ResellerAccount.id == reseller_id
    ).first()
    
    if not reseller:
        raise HTTPException(status_code=404, detail="Reseller not found")
    
    service = get_reseller_service(db)
    tier_config = service._get_tier_config(new_tier)
    
    reseller.tier = new_tier
    reseller.volume_discount = tier_config["discount"]
    reseller.custom_rates = tier_config["rates"]
    reseller.credit_limit = tier_config["credit_limit"]
    
    db.commit()
    
    return {
        "success": True,
        "reseller_id": reseller_id,
        "new_tier": new_tier,
        "new_discount": tier_config["discount"]
    }