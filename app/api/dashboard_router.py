"""Core Dashboard API Router - Minimal Implementation"""

from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func, desc

from app.core.database import get_db
from app.core.dependencies import get_current_user_id
from app.models.user import User
from app.models.notification import Notification

router = APIRouter(prefix="/api")


@router.get("/wallet/balance")
async def get_balance(
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """Get user wallet balance."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        return {"balance": 0.0, "credits": 0.0}
    
    return {
        "balance": float(user.credits or 0.0),
        "credits": float(user.credits or 0.0),
        "currency": "USD"
    }


@router.get("/wallet/transactions")
async def get_transactions(
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
    limit: int = 50,
    offset: int = 0
):
    """Get user transaction history."""
    try:
        from app.models.transaction import Transaction
        
        # Query transactions from database
        transactions = db.query(Transaction).filter(
            Transaction.user_id == user_id
        ).order_by(desc(Transaction.created_at)).limit(limit).offset(offset).all()
        
        # Get total count
        total = db.query(func.count(Transaction.id)).filter(
            Transaction.user_id == user_id
        ).scalar()
        
        return {
            "transactions": [
                {
                    "id": str(tx.id),
                    "type": tx.type,
                    "amount": float(tx.amount),
                    "description": tx.description,
                    "status": tx.status,
                    "created_at": tx.created_at.isoformat() if tx.created_at else None
                }
                for tx in transactions
            ],
            "total": total or 0,
            "page": (offset // limit) + 1,
            "limit": limit
        }
    except Exception as e:
        # Fallback to empty if table doesn't exist or error
        return {
            "transactions": [],
            "total": 0,
            "page": 1,
            "limit": limit
        }


@router.get("/analytics/summary")
async def get_analytics_summary(
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """Get user analytics summary."""
    user = db.query(User).filter(User.id == user_id).first()
    
    # TODO: Query actual verification and transaction data
    return {
        "total_verifications": 0,
        "successful_verifications": 0,
        "failed_verifications": 0,
        "total_spent": 0.0,
        "current_balance": float(user.credits or 0.0) if user else 0.0,
        "this_month": {
            "verifications": 0,
            "spent": 0.0
        },
        "last_30_days": {
            "verifications": 0,
            "spent": 0.0
        }
    }


@router.get("/dashboard/activity")
async def get_dashboard_activity(
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
    limit: int = 20
):
    """Get recent user activity."""
    # TODO: Query actual activity log when available
    return {
        "activities": [],
        "total": 0,
        "limit": limit
    }


@router.get("/verify/history")
async def get_verification_history(
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
    limit: int = 50,
    offset: int = 0,
    status: Optional[str] = None
):
    """Get user verification history."""
    try:
        from app.models.verification import Verification
        
        # Build query
        query = db.query(Verification).filter(Verification.user_id == user_id)
        
        # Add status filter if provided
        if status:
            query = query.filter(Verification.status == status)
        
        # Get verifications
        verifications = query.order_by(desc(Verification.created_at)).limit(limit).offset(offset).all()
        
        # Get total count
        total_query = db.query(func.count(Verification.id)).filter(Verification.user_id == user_id)
        if status:
            total_query = total_query.filter(Verification.status == status)
        total = total_query.scalar()
        
        return {
            "verifications": [
                {
                    "id": str(v.id),
                    "phone_number": v.phone_number,
                    "service": v.service,
                    "country": v.country,
                    "status": v.status,
                    "cost": float(v.cost) if v.cost else 0.0,
                    "created_at": v.created_at.isoformat() if v.created_at else None
                }
                for v in verifications
            ],
            "total": total or 0,
            "page": (offset // limit) + 1,
            "limit": limit
        }
    except Exception as e:
        # Fallback to empty if table doesn't exist
        return {
            "verifications": [],
            "total": 0,
            "page": 1,
            "limit": limit
        }


@router.get("/notifications")
async def get_notifications(
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
    limit: int = 50
):
    """Get user notifications."""
    try:
        notifications = db.query(Notification).filter(
            Notification.user_id == user_id
        ).order_by(desc(Notification.created_at)).limit(limit).all()
        
        return {
            "notifications": [
                {
                    "id": str(n.id),
                    "type": n.type,
                    "title": n.title,
                    "message": n.message,
                    "read": n.read,
                    "created_at": n.created_at.isoformat() if n.created_at else None
                }
                for n in notifications
            ],
            "total": len(notifications)
        }
    except Exception:
        # If notifications table doesn't exist yet
        return {"notifications": [], "total": 0}


@router.get("/notifications/unread")
async def get_unread_notifications_count(
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """Get unread notifications count."""
    try:
        count = db.query(func.count(Notification.id)).filter(
            Notification.user_id == user_id,
            Notification.read == False
        ).scalar()
        
        return {"unread_count": count or 0}
    except Exception:
        return {"unread_count": 0}


@router.get("/notifications/unread-count")
async def get_unread_count_alias(
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """Get unread notifications count (alias endpoint)."""
    try:
        count = db.query(func.count(Notification.id)).filter(
            Notification.user_id == user_id,
            Notification.read == False
        ).scalar()
        
        return {"count": count or 0, "unread_count": count or 0}
    except Exception:
        return {"count": 0, "unread_count": 0}


@router.get("/user/me")
async def get_current_user(
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """Get current user info."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        return {"error": "User not found"}
    
    return {
        "id": str(user.id),
        "email": user.email,
        "tier": getattr(user, 'subscription_tier', 'freemium'),
        "credits": float(user.credits or 0.0),
        "is_admin": user.is_admin,
        "created_at": user.created_at.isoformat() if user.created_at else None
    }


@router.get("/billing/balance")
async def get_billing_balance(
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """Get billing balance (alias for wallet/balance)."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        return {"balance": 0.0}
    
    return {
        "balance": float(user.credits or 0.0),
        "currency": "USD"
    }


@router.get("/tiers/current")
async def get_current_tier(
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """Get current user tier."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        return {"tier": "freemium"}
    
    tier = getattr(user, 'subscription_tier', 'freemium')
    return {
        "tier": tier,
        "name": tier.title(),
        "features": []
    }


@router.get("/user/settings")
async def get_user_settings(
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """Get user settings."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        return {}
    
    return {
        "email": user.email,
        "language": getattr(user, 'language', 'en'),
        "currency": getattr(user, 'currency', 'USD'),
        "notifications": {
            "email": True,
            "sms": False
        }
    }


@router.get("/countries")
async def get_countries():
    """Get available countries for SMS verification."""
    # Minimal country list - expand as needed
    return {
        "countries": [
            {"code": "US", "name": "United States", "available": True},
            {"code": "GB", "name": "United Kingdom", "available": True},
            {"code": "CA", "name": "Canada", "available": True},
            {"code": "AU", "name": "Australia", "available": True},
            {"code": "DE", "name": "Germany", "available": True},
            {"code": "FR", "name": "France", "available": True},
            {"code": "IN", "name": "India", "available": True},
            {"code": "BR", "name": "Brazil", "available": True},
        ]
    }


@router.get("/services")
async def get_services():
    """Get available services for SMS verification."""
    # Popular services
    return {
        "services": [
            {"id": "whatsapp", "name": "WhatsApp", "category": "messaging"},
            {"id": "telegram", "name": "Telegram", "category": "messaging"},
            {"id": "discord", "name": "Discord", "category": "gaming"},
            {"id": "instagram", "name": "Instagram", "category": "social"},
            {"id": "facebook", "name": "Facebook", "category": "social"},
            {"id": "twitter", "name": "Twitter/X", "category": "social"},
            {"id": "google", "name": "Google", "category": "tech"},
            {"id": "microsoft", "name": "Microsoft", "category": "tech"},
            {"id": "amazon", "name": "Amazon", "category": "ecommerce"},
            {"id": "uber", "name": "Uber", "category": "transport"},
        ],
        "total": 10
    }


# Admin endpoints (require admin check in production)
@router.get("/admin/kyc")
async def get_kyc_requests(
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
    limit: int = 50
):
    """Get KYC verification requests (admin only)."""
    # TODO: Add admin check
    return {
        "kyc_requests": [],
        "total": 0,
        "pending": 0,
        "approved": 0,
        "rejected": 0
    }


@router.get("/admin/support")
async def get_support_tickets(
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
    limit: int = 50
):
    """Get support tickets (admin only)."""
    # TODO: Add admin check
    return {
        "tickets": [],
        "total": 0,
        "open": 0,
        "closed": 0
    }
