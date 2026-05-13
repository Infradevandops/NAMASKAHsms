"""Billing history endpoints."""

from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user_id
from app.models.transaction import Transaction
from app.models.user import User

router = APIRouter(prefix="/api/billing", tags=["Billing"])


@router.get("/summary")
async def get_billing_summary(
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Get billing summary statistics."""
    from sqlalchemy import func

    total_spent = (
        db.query(func.sum(Transaction.amount))
        .filter(
            Transaction.user_id == user_id,
            Transaction.transaction_type.in_(
                ["deposit", "verification", "subscription"]
            ),
            Transaction.status == "completed",
        )
        .scalar()
        or 0
    )

    month_start = datetime.now().replace(
        day=1, hour=0, minute=0, second=0, microsecond=0
    )
    month_spent = (
        db.query(func.sum(Transaction.amount))
        .filter(
            Transaction.user_id == user_id,
            Transaction.transaction_type.in_(
                ["deposit", "verification", "subscription"]
            ),
            Transaction.status == "completed",
            Transaction.created_at >= month_start,
        )
        .scalar()
        or 0
    )

    total_transactions = (
        db.query(Transaction).filter(Transaction.user_id == user_id).count()
    )

    avg_transaction = total_spent / total_transactions if total_transactions > 0 else 0

    return {
        "total_spent": float(total_spent),
        "month_spent": float(month_spent),
        "total_transactions": total_transactions,
        "avg_transaction": float(avg_transaction),
    }


@router.get("/transactions")
async def get_transactions(
    limit: int = 20,
    offset: int = 0,
    type: Optional[str] = None,
    status: Optional[str] = None,
    from_date: Optional[str] = None,
    to_date: Optional[str] = None,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Get transaction history with filters."""
    query = db.query(Transaction).filter(Transaction.user_id == user_id)

    if type:
        query = query.filter(Transaction.transaction_type == type)
    if status:
        query = query.filter(Transaction.status == status)
    if from_date:
        query = query.filter(
            Transaction.created_at >= datetime.fromisoformat(from_date)
        )
    if to_date:
        query = query.filter(Transaction.created_at <= datetime.fromisoformat(to_date))

    total = query.count()
    transactions = (
        query.order_by(Transaction.created_at.desc()).limit(limit).offset(offset).all()
    )

    return {
        "transactions": [
            {
                "id": tx.id,
                "transaction_type": tx.transaction_type,
                "amount": float(tx.amount),
                "status": tx.status,
                "description": tx.description,
                "reference": tx.reference,
                "created_at": tx.created_at.isoformat(),
            }
            for tx in transactions
        ],
        "total": total,
        "limit": limit,
        "offset": offset,
    }


@router.get("/invoice/{transaction_id}")
async def get_invoice(
    transaction_id: str,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Get invoice for a transaction."""
    transaction = (
        db.query(Transaction)
        .filter(Transaction.id == transaction_id, Transaction.user_id == user_id)
        .first()
    )

    if not transaction:
        raise HTTPException(status_code=404, detail="Transaction not found")

    user = db.query(User).filter(User.id == user_id).first()

    return {
        "invoice_number": f"INV-{transaction.id[:8].upper()}",
        "transaction_id": transaction.id,
        "user_email": user.email,
        "user_id": user.id,
        "transaction_type": transaction.transaction_type,
        "amount": float(transaction.amount),
        "description": transaction.description
        or f"{transaction.transaction_type.title()} Transaction",
        "status": transaction.status,
        "created_at": transaction.created_at.isoformat(),
    }


@router.get("/invoice/{transaction_id}/download")
async def download_invoice(
    transaction_id: str,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Download invoice as PDF."""
    # Placeholder - would generate PDF in production
    return {"url": f"/invoices/{transaction_id}.pdf"}


@router.get("/export")
async def export_transactions(
    type: Optional[str] = None,
    status: Optional[str] = None,
    from_date: Optional[str] = None,
    to_date: Optional[str] = None,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Export transactions as CSV."""
    import csv
    import io

    from fastapi.responses import StreamingResponse

    query = db.query(Transaction).filter(Transaction.user_id == user_id)

    if type:
        query = query.filter(Transaction.transaction_type == type)
    if status:
        query = query.filter(Transaction.status == status)
    if from_date:
        query = query.filter(
            Transaction.created_at >= datetime.fromisoformat(from_date)
        )
    if to_date:
        query = query.filter(Transaction.created_at <= datetime.fromisoformat(to_date))

    transactions = query.order_by(Transaction.created_at.desc()).all()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(
        ["Date", "Transaction ID", "Type", "Description", "Amount", "Status"]
    )

    for tx in transactions:
        writer.writerow(
            [
                tx.created_at.strftime("%Y-%m-%d %H:%M:%S"),
                tx.id,
                tx.transaction_type,
                tx.description or "-",
                f"${tx.amount:.2f}",
                tx.status,
            ]
        )

    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={
            "Content-Disposition": f"attachment; filename=transactions_{datetime.now().strftime('%Y%m%d')}.csv"
        },
    )
