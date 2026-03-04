"""Core Dashboard API Router - Minimal Implementation"""

from datetime import datetime, timezone
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
    user = db.query(User).filter(User.id == user_id).first()

    try:
        from app.models.verification import Verification
        from app.models.transaction import Transaction
        from sqlalchemy import case

        verifications = db.query(Verification).filter(Verification.user_id == user_id).all()
        total = len(verifications)
        successful = sum(1 for v in verifications if v.status == 'completed')
        failed = sum(1 for v in verifications if v.status == 'failed')
        pending = sum(1 for v in verifications if v.status == 'pending')
        total_spent = sum(float(v.cost or 0) for v in verifications)
        avg_cost = total_spent / total if total else 0.0
        success_rate = (successful / total * 100) if total else 0.0

        # daily_verifications: last 30 days
        from datetime import timedelta
        today = datetime.now(timezone.utc).date()
        daily_map = {}
        for v in verifications:
            if v.created_at:
                d = v.created_at.date()
                daily_map[d] = daily_map.get(d, 0) + 1
        daily_verifications = [
            {"date": str(today - timedelta(days=i)), "count": daily_map.get(today - timedelta(days=i), 0)}
            for i in range(29, -1, -1)
        ]

        # spending_by_service
        service_spend = {}
        for v in verifications:
            svc = v.service_name or 'Unknown'
            service_spend[svc] = service_spend.get(svc, 0) + float(v.cost or 0)
        spending_by_service = [{'name': k, 'amount': v} for k, v in sorted(service_spend.items(), key=lambda x: -x[1])[:5]]

        # top_services
        service_stats = {}
        for v in verifications:
            svc = v.service_name or 'Unknown'
            if svc not in service_stats:
                service_stats[svc] = {'count': 0, 'success': 0, 'spent': 0.0}
            service_stats[svc]['count'] += 1
            if v.status == 'completed':
                service_stats[svc]['success'] += 1
            service_stats[svc]['spent'] += float(v.cost or 0)
        top_services = [
            {
                'name': k,
                'count': s['count'],
                'success_rate': (s['success'] / s['count'] * 100) if s['count'] else 0,
                'total_spent': s['spent']
            }
            for k, s in sorted(service_stats.items(), key=lambda x: -x[1]['count'])[:10]
        ]

        return {
            "total_verifications": total,
            "successful_verifications": successful,
            "failed_verifications": failed,
            "pending_verifications": pending,
            "total_spent": total_spent,
            "avg_cost": avg_cost,
            "success_rate": success_rate,
            "current_balance": float(user.credits or 0.0) if user else 0.0,
            "daily_verifications": daily_verifications,
            "spending_by_service": spending_by_service,
            "top_services": top_services,
        }
    except Exception:
        return {
            "total_verifications": 0,
            "successful_verifications": 0,
            "failed_verifications": 0,
            "pending_verifications": 0,
            "total_spent": 0.0,
            "avg_cost": 0.0,
            "success_rate": 0.0,
            "current_balance": float(user.credits or 0.0) if user else 0.0,
            "daily_verifications": [],
            "spending_by_service": [],
            "top_services": [],
        }


@router.get("/verify/history")
async def get_verification_history(
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
    limit: int = 50,
    offset: int = 0,
    status: Optional[str] = None
):
    try:
        from app.models.verification import Verification

        query = db.query(Verification).filter(Verification.user_id == user_id)
        if status:
            query = query.filter(Verification.status == status)

        verifications = query.order_by(desc(Verification.created_at)).limit(limit).offset(offset).all()

        total_query = db.query(func.count(Verification.id)).filter(Verification.user_id == user_id)
        if status:
            total_query = total_query.filter(Verification.status == status)
        total = total_query.scalar()

        return {
            "verifications": [
                {
                    "id": str(v.id),
                    "phone_number": v.phone_number,
                    "service": v.service_name,
                    "service_name": v.service_name,
                    "country": v.country,
                    "status": v.status,
                    "cost": float(v.cost) if v.cost else 0.0,
                    "sms_code": getattr(v, 'sms_code', None),
                    "sms_text": getattr(v, 'sms_text', None),
                    "carrier": getattr(v, 'carrier', None),
                    "created_at": v.created_at.isoformat() if v.created_at else None
                }
                for v in verifications
            ],
            "total": total or 0,
            "page": (offset // limit) + 1,
            "limit": limit
        }
    except Exception:
        return {"verifications": [], "total": 0, "page": 1, "limit": limit}


@router.get("/notifications/unread")
async def get_unread_notifications_count(
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    try:
        count = db.query(func.count(Notification.id)).filter(
            Notification.user_id == user_id,
            Notification.is_read == False
        ).scalar()
        return {"unread_count": count or 0}
    except Exception:
        return {"unread_count": 0}


@router.get("/notifications/unread-count")
async def get_unread_count_alias(
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    try:
        count = db.query(func.count(Notification.id)).filter(
            Notification.user_id == user_id,
            Notification.is_read == False
        ).scalar()
        return {"count": count or 0, "unread_count": count or 0}
    except Exception:
        return {"count": 0, "unread_count": 0}


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
