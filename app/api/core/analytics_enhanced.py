"""
Enhanced Analytics API with Real-time Calculations
Fixes all calculation issues and provides live data
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from datetime import datetime, timedelta
from typing import Dict, Any

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.models.verification import Verification
from app.models.transaction import Transaction

router = APIRouter(prefix="/api/analytics", tags=["analytics"])

@router.get("/summary")
async def get_analytics_summary(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Get real-time analytics summary with correct calculations
    """
    try:
        # Get all user verifications
        verifications = db.query(Verification).filter(
            Verification.user_id == current_user.id
        ).all()
        
        # Calculate totals
        total_verifications = len(verifications)
        successful_verifications = len([v for v in verifications if v.status == 'completed'])
        failed_verifications = len([v for v in verifications if v.status == 'failed'])
        pending_verifications = len([v for v in verifications if v.status in ['pending', 'processing']])
        
        # Calculate success rate
        success_rate = (successful_verifications / total_verifications) if total_verifications > 0 else 0
        
        # Calculate total spent from transactions
        spent_transactions = db.query(func.sum(Transaction.amount)).filter(
            and_(
                Transaction.user_id == current_user.id,
                Transaction.amount < 0,  # Negative amounts are spending
                Transaction.type.in_(['SMS Verification', 'Voice Verification', 'Rental'])
            )
        ).scalar() or 0
        
        total_spent = abs(spent_transactions)
        
        # Get recent activity (last 30 days)
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        recent_verifications = db.query(Verification).filter(
            and_(
                Verification.user_id == current_user.id,
                Verification.created_at >= thirty_days_ago
            )
        ).count()
        
        # Calculate average cost per verification
        avg_cost = total_spent / total_verifications if total_verifications > 0 else 0
        
        # Get monthly stats
        current_month = datetime.utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        monthly_verifications = db.query(Verification).filter(
            and_(
                Verification.user_id == current_user.id,
                Verification.created_at >= current_month
            )
        ).count()
        
        monthly_spent = abs(db.query(func.sum(Transaction.amount)).filter(
            and_(
                Transaction.user_id == current_user.id,
                Transaction.amount < 0,
                Transaction.created_at >= current_month
            )
        ).scalar() or 0)
        
        return {
            "total_verifications": total_verifications,
            "successful_verifications": successful_verifications,
            "failed_verifications": failed_verifications,
            "pending_verifications": pending_verifications,
            "success_rate": success_rate,
            "total_spent": total_spent,
            "revenue": total_spent,  # For backward compatibility
            "average_cost": avg_cost,
            "recent_activity": recent_verifications,
            "monthly_verifications": monthly_verifications,
            "monthly_spent": monthly_spent,
            "last_updated": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analytics calculation failed: {str(e)}")

@router.get("/real-time-stats")
async def get_real_time_stats(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Get real-time statistics for dashboard updates
    """
    try:
        # Get current balance
        current_balance = current_user.credits or 0
        
        # Get pending verifications count
        pending_count = db.query(Verification).filter(
            and_(
                Verification.user_id == current_user.id,
                Verification.status.in_(['pending', 'processing'])
            )
        ).count()
        
        # Get today's activity
        today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        today_verifications = db.query(Verification).filter(
            and_(
                Verification.user_id == current_user.id,
                Verification.created_at >= today
            )
        ).count()
        
        # Get last verification status
        last_verification = db.query(Verification).filter(
            Verification.user_id == current_user.id
        ).order_by(Verification.created_at.desc()).first()
        
        last_status = last_verification.status if last_verification else None
        
        return {
            "balance": current_balance,
            "pending_verifications": pending_count,
            "today_verifications": today_verifications,
            "last_verification_status": last_status,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Real-time stats failed: {str(e)}")

@router.get("/status-updates")
async def get_status_updates(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Get status updates for all pending verifications
    """
    try:
        pending_verifications = db.query(Verification).filter(
            and_(
                Verification.user_id == current_user.id,
                Verification.status.in_(['pending', 'processing'])
            )
        ).all()
        
        updates = []
        for verification in pending_verifications:
            updates.append({
                "id": verification.id,
                "status": verification.status,
                "phone_number": verification.phone_number,
                "service_name": verification.service_name,
                "created_at": verification.created_at.isoformat(),
                "updated_at": verification.updated_at.isoformat() if verification.updated_at else None
            })
        
        return {
            "updates": updates,
            "count": len(updates),
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Status updates failed: {str(e)}")