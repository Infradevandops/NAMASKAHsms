from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from datetime import datetime, date
from io import StringIO
import csv
from app.core.database import get_db
from app.models.user import User
from app.models.verification import Verification
from app.models.transaction import Transaction
from app.api.admin.dependencies import require_admin

router = APIRouter(prefix="/admin/export", tags=["admin-export"])


@router.get("/verifications")
async def export_verifications(
    start_date: str = Query(None),
    end_date: str = Query(None),
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Export verifications to CSV"""
    query = db.query(Verification)

    if start_date:
        query = query.filter(Verification.created_at >= datetime.fromisoformat(start_date))
    if end_date:
        query = query.filter(Verification.created_at <= datetime.fromisoformat(end_date))

    verifications = query.order_by(Verification.created_at.desc()).all()

    output = StringIO()
    writer = csv.DictWriter(
        output,
        fieldnames=[
            "id",
            "user_email",
            "service",
            "country",
            "phone",
            "status",
            "cost",
            "created_at",
            "completed_at",
        ],
    )
    writer.writeheader()

    for v in verifications:
        user = db.query(User).filter(User.id == v.user_id).first()
        writer.writerow(
            {
                "id": v.id,
                "user_email": user.email if user else "N/A",
                "service": v.service_name,
                "country": v.country_code,
                "phone": v.phone_number or "N/A",
                "status": v.status,
                "cost": v.cost,
                "created_at": v.created_at.isoformat() if v.created_at else "",
                "completed_at": v.completed_at.isoformat() if v.completed_at else "",
            }
        )

    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=verifications_{date.today()}.csv"},
    )


@router.get("/users")
async def export_users(
    start_date: str = Query(None),
    end_date: str = Query(None),
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Export users to CSV"""
    query = db.query(User)

    if start_date:
        query = query.filter(User.created_at >= datetime.fromisoformat(start_date))
    if end_date:
        query = query.filter(User.created_at <= datetime.fromisoformat(end_date))

    users = query.order_by(User.created_at.desc()).all()

    output = StringIO()
    writer = csv.DictWriter(
        output, fieldnames=["id", "email", "tier", "credits", "is_admin", "created_at"]
    )
    writer.writeheader()

    for u in users:
        writer.writerow(
            {
                "id": u.id,
                "email": u.email,
                "tier": u.tier,
                "credits": u.credits,
                "is_admin": u.is_admin,
                "created_at": u.created_at.isoformat() if u.created_at else "",
            }
        )

    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=users_{date.today()}.csv"},
    )


@router.get("/revenue")
async def export_revenue(
    start_date: str = Query(None),
    end_date: str = Query(None),
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Export revenue transactions to CSV"""
    query = db.query(Transaction).filter(Transaction.type == "credit")

    if start_date:
        query = query.filter(Transaction.created_at >= datetime.fromisoformat(start_date))
    if end_date:
        query = query.filter(Transaction.created_at <= datetime.fromisoformat(end_date))

    transactions = query.order_by(Transaction.created_at.desc()).all()

    output = StringIO()
    writer = csv.DictWriter(
        output, fieldnames=["id", "user_email", "amount", "type", "description", "created_at"]
    )
    writer.writeheader()

    for t in transactions:
        writer.writerow(
            {
                "id": t.id,
                "user_email": t.user.email if t.user else "N/A",
                "amount": t.amount,
                "type": t.transaction_type,
                "description": t.description or "",
                "created_at": t.created_at.isoformat() if t.created_at else "",
            }
        )

    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=revenue_{date.today()}.csv"},
    )
