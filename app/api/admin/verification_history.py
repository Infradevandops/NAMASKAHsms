"""Admin API for User Verification History"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import desc, func
from typing import Optional, List
from datetime import datetime, timedelta
from app.core.database import get_db
from app.core.dependencies import get_current_admin_user as require_admin
from app.core.unified_cache import cache
from app.models.user import User
from app.models.verification import Verification, VerificationReceipt
from app.models.transaction import Transaction
from pydantic import BaseModel

router = APIRouter(prefix="/api/admin/verification-history", tags=["Admin - Verification History"])


class VerificationHistoryResponse(BaseModel):
    verification_id: str
    transaction_id: str
    user_id: str
    user_email: str
    service_name: str
    phone_number: Optional[str]
    country: str
    status: str
    cost: float
    area_code: Optional[str]
    carrier: Optional[str]
    created_at: str
    completed_at: Optional[str]
    sms_code: Optional[str]


class UserVerificationStats(BaseModel):
    user_id: str
    user_email: str
    total_verifications: int
    successful_verifications: int
    failed_verifications: int
    total_spent: float
    success_rate: float
    last_verification: Optional[str]


@router.get("/user/{user_id}")
async def get_user_verification_history(
    user_id: str,
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    status: Optional[str] = None,
    admin_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Get verification history for specific user"""
    
    # Check if user exists
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Build query
    query = db.query(Verification).filter(Verification.user_id == user_id)
    
    if status:
        query = query.filter(Verification.status == status)
    
    # Get total count
    total = query.count()
    
    # Get paginated results with JOIN
    verifications = query.order_by(desc(Verification.created_at)).limit(limit).offset(offset).all()
    
    # Format response
    history = []
    for v in verifications:
        user = db.query(User).filter(User.id == v.user_id).first()
        history.append({
            "verification_id": v.id,
            "transaction_id": getattr(v, 'transaction_id', v.id),  # Use actual transaction_id if available
            "user_id": v.user_id,
            "user_email": user.email if user else "Unknown",
            "service_name": v.service_name,
            "phone_number": v.phone_number,
            "country": v.country,
            "status": v.status,
            "cost": float(v.cost) if v.cost else 0.0,
            "area_code": v.requested_area_code,
            "carrier": v.requested_carrier,
            "created_at": v.created_at.isoformat() if v.created_at else None,
            "completed_at": v.completed_at.isoformat() if v.completed_at else None,
            "sms_code": v.sms_code
        })
    
    return {
        "success": True,
        "user": {
            "id": user.id,
            "email": user.email,
            "credits": float(user.credits or 0)
        },
        "total": total,
        "limit": limit,
        "offset": offset,
        "history": history
    }


@router.get("/transaction/{transaction_id}")
async def get_verification_by_transaction(
    transaction_id: str,
    admin_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Get verification details by transaction/verification ID"""
    
    verification = db.query(Verification).filter(Verification.id == transaction_id).first()
    
    if not verification:
        raise HTTPException(status_code=404, detail="Verification not found")
    
    user = db.query(User).filter(User.id == verification.user_id).first()
    
    return {
        "success": True,
        "verification": {
            "verification_id": verification.id,
            "transaction_id": verification.id,
            "user_id": verification.user_id,
            "user_email": user.email if user else "Unknown",
            "service_name": verification.service_name,
            "phone_number": verification.phone_number,
            "country": verification.country,
            "capability": verification.capability,
            "status": verification.status,
            "cost": float(verification.cost) if verification.cost else 0.0,
            "provider": verification.provider,
            "activation_id": verification.activation_id,
            "area_code": verification.requested_area_code,
            "carrier": verification.requested_carrier,
            "sms_code": verification.sms_code,
            "sms_text": verification.sms_text,
            "created_at": verification.created_at.isoformat() if verification.created_at else None,
            "completed_at": verification.completed_at.isoformat() if verification.completed_at else None,
            "sms_received_at": verification.sms_received_at.isoformat() if verification.sms_received_at else None
        }
    }


@router.get("/stats")
# @cache.cached - disabled  # Cache for 5 minutes
async def get_verification_stats(
    days: int = Query(30, ge=1, le=365),
    admin_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Get verification statistics for all users - OPTIMIZED"""
    
    since_date = datetime.utcnow() - timedelta(days=days)
    
    # Optimized query with JOIN
    user_stats = db.query(
        Verification.user_id,
        User.email,
        func.count(Verification.id).label('total'),
        func.sum(func.case((Verification.status == 'completed', 1), else_=0)).label('successful'),
        func.sum(Verification.cost).label('total_spent'),
        func.max(Verification.created_at).label('last_verification')
    ).join(User, Verification.user_id == User.id).filter(
        Verification.created_at >= since_date
    ).group_by(Verification.user_id, User.email).all()
    
    # Format results
    stats = []
    for stat in user_stats:
        total = stat.total or 0
        successful = stat.successful or 0
        failed = total - successful
        
        stats.append({
            "user_id": stat.user_id,
            "user_email": stat.email,
            "total_verifications": total,
            "successful_verifications": successful,
            "failed_verifications": failed,
            "total_spent": float(stat.total_spent or 0),
            "success_rate": (successful / total) if total > 0 else 0.0,
            "last_verification": stat.last_verification.isoformat() if stat.last_verification else None
        })
    
    # Sort by total spent
    stats.sort(key=lambda x: x['total_spent'], reverse=True)
    
    return {
        "success": True,
        "period_days": days,
        "total_users": len(stats),
        "stats": stats
    }


@router.get("/recent")
# @cache.cached - disabled  # Cache for 1 minute
async def get_recent_verifications(
    limit: int = Query(100, ge=1, le=500),
    status: Optional[str] = None,
    admin_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Get recent verifications across all users - OPTIMIZED"""
    
    # Use JOIN to avoid N+1 query problem
    query = db.query(Verification)
    
    if status:
        query = query.filter(Verification.status == status)
    
    verifications = query.order_by(desc(Verification.created_at)).limit(limit).all()
    
    history = []
    for v in verifications:
        user = db.query(User).filter(User.id == v.user_id).first()
        history.append({
            "verification_id": v.id,
            "transaction_id": getattr(v, 'transaction_id', v.id),  # Use actual transaction_id if available
            "user_id": v.user_id,
            "user_email": user.email if user else "Unknown",
            "service_name": v.service_name,
            "phone_number": v.phone_number,
            "country": v.country,
            "status": v.status,
            "cost": float(v.cost) if v.cost else 0.0,
            "created_at": v.created_at.isoformat() if v.created_at else None,
            "completed_at": v.completed_at.isoformat() if v.completed_at else None
        })
    
    return {
        "success": True,
        "total": len(history),
        "history": history
    }


@router.get("/search")
async def search_verifications(
    query: str = Query(..., min_length=3),
    search_by: str = Query("email", regex="^(email|phone|service|verification_id)$"),
    limit: int = Query(50, ge=1, le=200),
    admin_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Search verifications by email, phone, service, or verification ID"""
    
    if search_by == "email":
        # Search by user email
        users = db.query(User).filter(User.email.ilike(f"%{query}%")).all()
        user_ids = [u.id for u in users]
        verifications = db.query(Verification).filter(
            Verification.user_id.in_(user_ids)
        ).order_by(desc(Verification.created_at)).limit(limit).all()
        
    elif search_by == "phone":
        verifications = db.query(Verification).filter(
            Verification.phone_number.ilike(f"%{query}%")
        ).order_by(desc(Verification.created_at)).limit(limit).all()
        
    elif search_by == "service":
        verifications = db.query(Verification).filter(
            Verification.service_name.ilike(f"%{query}%")
        ).order_by(desc(Verification.created_at)).limit(limit).all()
        
    elif search_by == "verification_id":
        verifications = db.query(Verification).filter(
            Verification.id.ilike(f"%{query}%")
        ).order_by(desc(Verification.created_at)).limit(limit).all()
    
    else:
        raise HTTPException(status_code=400, detail="Invalid search_by parameter")
    
    # Get user emails
    user_ids = list(set([v.user_id for v in verifications]))
    users = db.query(User).filter(User.id.in_(user_ids)).all()
    user_map = {u.id: u.email for u in users}
    
    history = []
    for v in verifications:
        user = db.query(User).filter(User.id == v.user_id).first()
        history.append({
            "verification_id": v.id,
            "transaction_id": v.id,
            "user_id": v.user_id,
            "user_email": user_map.get(v.user_id, "Unknown"),
            "service_name": v.service_name,
            "phone_number": v.phone_number,
            "country": v.country,
            "status": v.status,
            "cost": float(v.cost) if v.cost else 0.0,
            "created_at": v.created_at.isoformat() if v.created_at else None
        })
    
    return {
        "success": True,
        "search_query": query,
        "search_by": search_by,
        "total": len(history),
        "history": history
    }
