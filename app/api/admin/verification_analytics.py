"""Admin verification analytics endpoints - OPTIMIZED"""


from datetime import datetime, timedelta
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import desc, func
from sqlalchemy.orm import Session, joinedload
from app.core.database import get_db
from app.core.dependencies import get_current_user_id
from app.models.transaction import Transaction
from app.models.user import User
from app.models.verification import Verification

router = APIRouter(prefix="/admin/verifications", tags=["admin-analytics"])


def verify_admin(user_id: str, db: Session):

    """Verify user is admin"""
    user = db.query(User).filter(User.id == user_id).first()
if not user or not user.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")
    return user


@router.get("/all")
async def get_all_verifications(
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
    limit: int = Query(50, le=500),
    offset: int = Query(0, ge=0),
    status: Optional[str] = None,
    search_user: Optional[str] = None,
):
    """Get all verifications - OPTIMIZED with JOINs"""
    verify_admin(user_id, db)

    # Optimized query with JOINs (no N+1 problem)
    query = db.query(Verification).join(User).order_by(desc(Verification.created_at))

if status:
        query = query.filter(Verification.status == status)

if search_user:
        query = query.filter((User.email.ilike(f"%{search_user}%")) | (User.id == search_user))

    total = query.count()

    # Use joinedload to fetch related data in single query
    verifications = query.options(joinedload(Verification.user)).limit(limit).offset(offset).all()

    results = []
for v in verifications:
        results.append(
            {
                "verification_id": v.id,
                "transaction_id": getattr(v, "transaction_id", None),
                "user_id": v.user_id,
                "user_email": v.user.email if v.user else "Unknown",
                "service_name": v.service_name,
                "phone_number": v.phone_number,
                "country": v.country,
                "status": v.status,
                "cost": float(v.cost) if v.cost else 0,
                "provider": v.provider,
                "created_at": v.created_at.isoformat() if v.created_at else None,
            }
        )

    return {"total": total, "limit": limit, "offset": offset, "verifications": results}


@router.get("/stats")
async def get_verification_stats(user_id: str = Depends(get_current_user_id), db: Session = Depends(get_db)):
    """Get verification statistics - CACHED"""
    verify_admin(user_id, db)

    # Optimized aggregation queries
    stats = db.query(
        func.count(Verification.id).label("total"),
        func.sum(func.case((Verification.status == "completed", 1), else_=0)).label("completed"),
        func.sum(func.case((Verification.status == "pending", 1), else_=0)).label("pending"),
        func.sum(func.case((Verification.status == "failed", 1), else_=0)).label("failed"),
        func.sum(Verification.cost).label("revenue"),
    ).first()

    total = stats.total or 0
    completed = stats.completed or 0

    # Top users - optimized
    top_users = (
        db.query(
            Verification.user_id,
            User.email,
            func.count(Verification.id).label("count"),
            func.sum(Verification.cost).label("spent"),
        )
        .join(User)
        .group_by(Verification.user_id, User.email)
        .order_by(desc("count"))
        .limit(10)
        .all()
    )

    # Top services - optimized
    top_services = (
        db.query(Verification.service_name, func.count(Verification.id).label("count"))
        .group_by(Verification.service_name)
        .order_by(desc("count"))
        .limit(10)
        .all()
    )

    return {
        "total_verifications": total,
        "completed": completed,
        "pending": stats.pending or 0,
        "failed": stats.failed or 0,
        "success_rate": (completed / total * 100) if total > 0 else 0,
        "total_revenue": float(stats.revenue or 0),
        "top_users": [
            {
                "user_id": u,
                "email": e,
                "verification_count": c,
                "total_spent": float(s or 0),
            }
for u, e, c, s in top_users
        ],
        "top_services": [{"service": s, "count": c} for s, c in top_services],
    }


@router.get("/user/{user_id_param}")
async def get_user_verifications(
    user_id_param: str,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
    limit: int = Query(50, le=500),
):
    """Get all verifications for a specific user"""
    verify_admin(user_id, db)

    user = db.query(User).filter(User.id == user_id_param).first()
if not user:
        raise HTTPException(status_code=404, detail="User not found")

    verifications = (
        db.query(Verification)
        .filter(Verification.user_id == user_id_param)
        .order_by(desc(Verification.created_at))
        .limit(limit)
        .all()
    )

    results = []
for v in verifications:
        transaction = (
            db.query(Transaction)
            .filter(
                Transaction.user_id == v.user_id,
                Transaction.created_at >= v.created_at - timedelta(seconds=5),
                Transaction.created_at <= v.created_at + timedelta(seconds=5),
            )
            .first()
        )

        results.append(
            {
                "verification_id": v.id,
                "transaction_id": transaction.id if transaction else None,
                "service_name": v.service_name,
                "phone_number": v.phone_number,
                "status": v.status,
                "cost": float(v.cost) if v.cost else 0,
                "created_at": v.created_at.isoformat() if v.created_at else None,
            }
        )

    return {
        "user_id": user_id_param,
        "user_email": user.email,
        "total_verifications": len(results),
        "verifications": results,
    }


@router.get("/export")
async def export_verifications(
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
):
    """Export all verifications as CSV data"""
    verify_admin(user_id, db)

    query = db.query(Verification).order_by(desc(Verification.created_at))

if start_date:
        query = query.filter(Verification.created_at >= datetime.fromisoformat(start_date))
if end_date:
        query = query.filter(Verification.created_at <= datetime.fromisoformat(end_date))

    verifications = query.all()

    csv_data = "Verification ID,Transaction ID,User ID,User Email,Service,Phone,Country,Status,Cost,Created At\n"

for v in verifications:
        user = db.query(User).filter(User.id == v.user_id).first()
        transaction = (
            db.query(Transaction)
            .filter(
                Transaction.user_id == v.user_id,
                Transaction.created_at >= v.created_at - timedelta(seconds=5),
                Transaction.created_at <= v.created_at + timedelta(seconds=5),
            )
            .first()
        )

        csv_data += f"{v.id},{transaction.id if transaction else 'N/A'},{v.user_id},{user.email if user else 'Unknown'},{v.service_name},{v.phone_number},{v.country},{v.status},{v.cost},{v.created_at}\n"

    return {"csv_data": csv_data, "total_records": len(verifications)}
