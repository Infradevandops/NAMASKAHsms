"""Invoice endpoints — downloadable receipts."""

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.dependencies import get_current_user_id
from app.models.transaction import Transaction
from app.models.user import User

router = APIRouter()


@router.get("/{transaction_id}")
async def download_invoice(
    transaction_id: str,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    tx = db.query(Transaction).filter(
        Transaction.id == transaction_id,
        Transaction.user_id == user_id
    ).first()
    if not tx:
        raise HTTPException(status_code=404, detail="Transaction not found")

    user = db.query(User).filter(User.id == user_id).first()

    receipt = {
        "invoice_id": f"INV-{tx.id}",
        "reference": getattr(tx, "reference", tx.id),
        "date": tx.created_at.isoformat() if tx.created_at else None,
        "amount": abs(tx.amount),
        "currency": "USD",
        "description": tx.description or tx.transaction_type,
        "status": tx.status,
        "billed_to": user.email if user else None,
        "platform": "Namaskah",
    }
    return JSONResponse(
        content=receipt,
        headers={"Content-Disposition": f"attachment; filename=invoice-{tx.id}.json"}
    )
