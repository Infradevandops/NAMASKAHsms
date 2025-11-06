"""Wallet API router for payments and transactions."""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user_id
from app.core.exceptions import PaymentError, ValidationError
from app.models.transaction import Transaction
from app.models.user import User
from app.schemas import (
    PaymentInitialize,
    PaymentInitializeResponse,
    PaymentVerify,
    PaymentVerifyResponse,
    TransactionHistoryResponse,
    TransactionResponse,
    WalletBalanceResponse,
)
from app.services import get_payment_service

router = APIRouter(prefix="/wallet", tags=["Wallet"])


@router.get("/balance", response_model=WalletBalanceResponse)
def get_wallet_balance(
    user_id: str = Depends(get_current_user_id), db: Session = Depends(get_db)
):
    """Get current wallet balance."""
    user = db.query(User).filter(User.id == user_id).first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return WalletBalanceResponse(
        credits=user.credits,
        credits_usd=user.credits * 2.0,  # 1 credit = $2 USD
        free_verifications=user.free_verifications,
    )


@router.post("/paystack/initialize", response_model=PaymentInitializeResponse)
async def initialize_paystack_payment(
    payment_data: PaymentInitialize,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Initialize Paystack payment."""
    user = db.query(User).filter(User.id == user_id).first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    payment_service = get_payment_service(db)

    try:
        result = await payment_service.initialize_payment(
            user_id=user_id, email=user.email, amount_usd=payment_data.amount_usd
        )

        return PaymentInitializeResponse(**result)

    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except PaymentError as e:
        raise HTTPException(status_code=402, detail=str(e))


@router.post("/paystack/verify", response_model=PaymentVerifyResponse)
async def verify_paystack_payment(
    verify_data: PaymentVerify,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Verify Paystack payment status."""
    payment_service = get_payment_service(db)

    try:
        result = await payment_service.verify_payment(verify_data.reference)

        if result["status"] == "success":
            # Payment successful, credits should already be added via webhook
            user = db.query(User).filter(User.id == user_id).first()

            return PaymentVerifyResponse(
                status="success",
                amount_credited=result.get("metadata", {}).get("namaskah_amount", 0),
                new_balance=user.credits,
                reference=verify_data.reference,
                message="Payment verified and credited successfully",
            )
        else:
            return PaymentVerifyResponse(
                status="failed",
                amount_credited=0,
                new_balance=0,
                reference=verify_data.reference,
                message=f"Payment failed: {result.get('status', 'Unknown error')}",
            )

    except PaymentError as e:
        raise HTTPException(status_code=402, detail=str(e))


@router.post("/paystack/webhook")
async def paystack_webhook(request: Request, db: Session = Depends(get_db)):
    """Handle Paystack webhook notifications."""
    from app.services.webhook_service import WebhookService

    # Get signature and body
    signature = request.headers.get("x-paystack-signature")
    body = await request.body()

    if not signature:
        raise HTTPException(status_code=400, detail="Missing signature")

    webhook_service = WebhookService(db)

    # Verify webhook signature
    if not webhook_service.verify_signature(body, signature):
        raise HTTPException(status_code=400, detail="Invalid signature")

    # Parse webhook data
    try:
        webhook_data = await request.json()
    except (ValueError, TypeError, AttributeError):
        raise HTTPException(status_code=400, detail="Invalid JSON")

    # Process webhook
    try:
        success = webhook_service.process_payment_webhook(webhook_data)

        if success:
            return {"status": "success"}
        else:
            return {"status": "ignored"}

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Webhook processing failed: {str(e)}"
        )


@router.get("/transactions", response_model=TransactionHistoryResponse)
def get_transaction_history(
    user_id: str = Depends(get_current_user_id),
    transaction_type: Optional[str] = Query(
        None, description="Filter by type: credit or debit"
    ),
    limit: int = Query(50, le=100, description="Number of results"),
    skip: int = Query(0, description="Number of results to skip"),
    db: Session = Depends(get_db),
):
    """Get user's transaction history."""
    query = db.query(Transaction).filter(Transaction.user_id == user_id)

    if transaction_type:
        query = query.filter(Transaction.type == transaction_type)

    total = query.count()
    transactions = (
        query.order_by(Transaction.created_at.desc()).offset(skip).limit(limit).all()
    )

    return TransactionHistoryResponse(
        transactions=[TransactionResponse.from_orm(t) for t in transactions],
        total_count=total,
    )


@router.get("/transactions/export")
async def export_transactions(
    user_id: str = Depends(get_current_user_id),
    export_format: str = Query("csv", description="Export format: csv or json"),
    db: Session = Depends(get_db),
):
    """Export user's transaction history."""
    import csv
    import io
    import json

    from fastapi.responses import StreamingResponse

    transactions = (
        db.query(Transaction)
        .filter(Transaction.user_id == user_id)
        .order_by(Transaction.created_at.desc())
        .all()
    )

    if export_format == "csv":
        output = io.StringIO()
        writer = csv.writer(output)

        # Header
        writer.writerow(["Date", "Type", "Amount (N)", "Description"])

        # Data
        for t in transactions:
            writer.writerow(
                [
                    t.created_at.strftime("%Y-%m-%d %H:%M:%S"),
                    t.type.upper(),
                    f"{t.amount:.2f}",
                    t.description,
                ]
            )

        output.seek(0)
        return StreamingResponse(
            iter([output.getvalue()]),
            media_type="text/csv",
            headers={
                "Content-Disposition": f"attachment; filename=transactions_{user_id}.csv"
            },
        )

    elif export_format == "json":
        data = [
            {
                "date": t.created_at.isoformat(),
                "type": t.type,
                "amount": t.amount,
                "description": t.description,
            }
            for t in transactions
        ]

        output = io.StringIO()
        json.dump(data, output, indent=2)
        output.seek(0)

        return StreamingResponse(
            iter([output.getvalue()]),
            media_type="application/json",
            headers={
                "Content-Disposition": f"attachment; filename=transactions_{user_id}.json"
            },
        )

    else:
        raise HTTPException(
            status_code=400, detail="Invalid format. Use 'csv' or 'json'"
        )


@router.get("/spending-summary")
def get_spending_summary(
    user_id: str = Depends(get_current_user_id),
    days: int = Query(30, description="Number of days to analyze"),
    db: Session = Depends(get_db),
):
    """Get spending summary and analytics."""
    from datetime import datetime, timedelta, timezone

    from sqlalchemy import func

    start_date = datetime.now(timezone.utc) - timedelta(days=days)

    # Total spent in period
    total_spent = (
        db.query(func.sum(Transaction.amount))
        .filter(
            Transaction.user_id == user_id,
            Transaction.type == "debit",
            Transaction.created_at >= start_date,
        )
        .scalar()
        or 0
    )

    # Total funded in period
    total_funded = (
        db.query(func.sum(Transaction.amount))
        .filter(
            Transaction.user_id == user_id,
            Transaction.type == "credit",
            Transaction.created_at >= start_date,
        )
        .scalar()
        or 0
    )

    # Daily spending
    daily_spending = []
    for i in range(days):
        day = datetime.now(timezone.utc) - timedelta(days=i)
        day_start = day.replace(hour=0, minute=0, second=0, microsecond=0)
        day_end = day_start + timedelta(days=1)

        day_spent = (
            db.query(func.sum(Transaction.amount))
            .filter(
                Transaction.user_id == user_id,
                Transaction.type == "debit",
                Transaction.created_at >= day_start,
                Transaction.created_at < day_end,
            )
            .scalar()
            or 0
        )

        daily_spending.append(
            {"date": day_start.strftime("%Y-%m-%d"), "amount": abs(day_spent)}
        )

    # Get current balance
    user = db.query(User).filter(User.id == user_id).first()

    return {
        "period_days": days,
        "total_spent": abs(total_spent),
        "total_funded": total_funded,
        "net_change": total_funded - abs(total_spent),
        "current_balance": user.credits if user else 0,
        "daily_spending": list(reversed(daily_spending)),
        "avg_daily_spending": abs(total_spent) / days if days > 0 else 0,
    }
