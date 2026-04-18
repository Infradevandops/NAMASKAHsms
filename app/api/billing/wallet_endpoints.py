"""
Unified Wallet & Crypto Endpoints.
Handles transaction intents, crypto confirmations, and high-density wallet analytics.
"""

from datetime import datetime, timezone
from typing import Optional, Dict, Any
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Query, Response
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.database import get_db

from app.core.dependencies import get_current_user_id
from app.models.transaction import PaymentLog, Transaction
from app.models.balance_transaction import BalanceTransaction
from app.models.user import User
from app.core.config import settings
from app.core.logging import get_logger
from app.services.financial_statements_service import FinancialStatementsService
from sqlalchemy import func


logger = get_logger(__name__)
router = APIRouter()


class CryptoIntentRequest(BaseModel):
    amount_usd: float = Field(..., gt=0)
    currency: str = Field(..., pattern="^(btc|eth|sol|ltc)$")
    crypto_amount: float
    address: str


class CryptoConfirmRequest(BaseModel):
    intent_id: str
    transaction_hash: Optional[str] = None


@router.get("/crypto/addresses")
async def get_crypto_addresses(user_id: str = Depends(get_current_user_id)):
    """Returns the secure institutional addresses for crypto settlement."""
    return {
        "btc_address": settings.btc_address,
        "eth_address": settings.eth_address,
        "sol_address": settings.sol_address,
        "ltc_address": settings.ltc_address,
    }


@router.post("/crypto/intent")
async def record_crypto_intent(
    request: CryptoIntentRequest,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Records a user's intent to pay with crypto."""
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        reference = f"crypto_{request.currency}_{uuid4().hex[:8]}"

        # Create a PaymentLog entry for the intent
        intent = PaymentLog(
            user_id=user_id,
            email=user.email,
            reference=reference,
            amount_usd=request.amount_usd,
            amount_ngn=0.0,  # Not applicable for crypto
            namaskah_amount=request.amount_usd,
            payment_method=f"crypto_{request.currency}",
            state="pending",
            processing_started_at=datetime.now(timezone.utc),
            error_message=f"Address: {request.address} | Expected Crypto: {request.crypto_amount}",
        )

        db.add(intent)

        # Also create a placeholder Transaction so it shows up in "Pending Transactions"
        tx = Transaction(
            user_id=user_id,
            amount=request.amount_usd,
            type="credit_pending",
            description=f"Crypto Intent: {request.crypto_amount} {request.currency.upper()}",
            status="pending",
            reference=reference,
            created_at=datetime.now(timezone.utc),
        )
        db.add(tx)

        db.commit()

        return {
            "status": "success",
            "intent_id": reference,
            "message": "Payment intent recorded. Please send the exact amount.",
        }
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to record crypto intent: {e}")
        raise HTTPException(status_code=500, detail="Failed to record payment intent")


@router.post("/crypto/confirm")
async def confirm_crypto_payment(
    request: CryptoConfirmRequest,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Moves a crypto intent to 'review_pending' for admin verification."""
    intent = (
        db.query(PaymentLog)
        .filter(
            PaymentLog.reference == request.intent_id, PaymentLog.user_id == user_id
        )
        .first()
    )

    if not intent:
        raise HTTPException(status_code=404, detail="Intent not found")

    if intent.state != "pending":
        return {
            "status": "error",
            "message": f"Intent is already in {intent.state} state",
        }

    intent.state = "processing"  # 'processing' acts as review_pending
    intent.error_message = (
        f"{intent.error_message} | Hash: {request.transaction_hash or 'None'}"
    )

    # Update the associated transaction record
    tx = (
        db.query(Transaction).filter(Transaction.reference == request.intent_id).first()
    )
    if tx:
        tx.description = f"{tx.description} (Under Review)"

    db.commit()

    # Notify admin (logic omitted for brevity, but could be integrated with notification_dispatcher)

    return {
        "status": "success",
        "message": "Payment notification received. Admin will verify shortly.",
    }


@router.get("/stats")
async def get_wallet_stats(
    user_id: str = Depends(get_current_user_id), db: Session = Depends(get_db)
):
    """High-density wallet stats for the new UI."""
    user = db.query(User).filter(User.id == user_id).first()

    # Get monthly spend accurately from the BalanceTransaction ledger
    month_start = datetime.now(timezone.utc).replace(
        day=1, hour=0, minute=0, second=0, microsecond=0
    )

    monthly_spend = (
        db.query(func.sum(BalanceTransaction.amount))
        .filter(
            BalanceTransaction.user_id == user_id,
            BalanceTransaction.type == "debit",
            BalanceTransaction.created_at >= month_start,
        )
        .scalar()
        or 0.0
    )

    # Calculate total refunds for perfect financial balancing
    from app.core.constants import TransactionType

    total_refunds = (
        db.query(func.sum(BalanceTransaction.amount))
        .filter(
            BalanceTransaction.user_id == user_id,
            BalanceTransaction.type == TransactionType.REFUND,
        )
        .scalar()
        or 0.0
    )

    # We negate the debit sum for positive display in the UI
    monthly_spend = abs(float(monthly_spend))

    total_spend = (
        db.query(func.sum(BalanceTransaction.amount))
        .filter(
            BalanceTransaction.user_id == user_id, BalanceTransaction.type == "debit"
        )
        .scalar()
        or 0.0
    )
    total_spend = abs(float(total_spend))

    pending_deposits = (
        db.query(func.count(PaymentLog.id))
        .filter(
            PaymentLog.user_id == user_id,
            PaymentLog.state.in_(["pending", "processing"]),
        )
        .scalar()
        or 0
    )

    return {
        "balance": float(user.credits or 0.0),
        "monthly_spent": float(monthly_spend),
        "total_spent": float(total_spend),
        "total_refunds": float(total_refunds),
        "net_spent": float(total_spend) - float(total_refunds),
        "pending_deposits": int(pending_deposits),
        "currency": "USD",
        "last_synced": datetime.now(timezone.utc).isoformat(),
    }


@router.get("/export/csv")
async def export_wallet_csv(
    user_id: str = Depends(get_current_user_id), db: Session = Depends(get_db)
):
    """Generates and streams a CSV audit trail for the user."""
    try:
        service = FinancialStatementsService(db)
        csv_content = await service.export_user_transactions_csv(user_id)

        filename = f"namaskah_wallet_audit_{datetime.now().strftime('%Y%m%d')}.csv"

        return Response(
            content=csv_content,
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename={filename}"},
        )
    except Exception as e:
        logger.error(f"CSV Export failed for {user_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate export")
