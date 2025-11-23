"""Wallet API router - Updated Error Handling"""
from app.core.dependencies import get_current_user_id
from typing import Optional
from datetime import datetime, timedelta, timezone
import csv
import io
import json

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy import func

from app.core.database import get_db
    PaymentError,
    InvalidInputError,
    ResourceNotFoundError,
)
    PaymentInitialize,
    PaymentInitializeResponse,
    PaymentVerify,
    PaymentVerifyResponse,
    TransactionHistoryResponse,
    TransactionResponse,
    WalletBalanceResponse,
)

logger = get_logger(__name__)
router = APIRouter(prefix="/wallet", tags=["Wallet"])


@router.get("/balance", response_model=WalletBalanceResponse)
def get_wallet_balance(
    user_id: str = Depends(get_current_user_id), db: Session = Depends(get_db)
):
    """Get current wallet balance."""
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise ResourceNotFoundError("User not found")

        return WalletBalanceResponse(
            credits=user.credits,
            credits_usd=user.credits,
            free_verifications=user.free_verifications,
        )
    except ResourceNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to get wallet balance: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve balance")


@router.post("/paystack/initialize", response_model=PaymentInitializeResponse)
async def initialize_paystack_payment(
    payment_data: PaymentInitialize,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Initialize Paystack payment."""
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise ResourceNotFoundError("User not found")

        payment_service = get_payment_service(db)
        result = await payment_service.initialize_payment(
            user_id=user_id, email=user.email, amount_usd=payment_data.amount_usd
        )
        return PaymentInitializeResponse(**result)

    except ResourceNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except InvalidInputError as e:
        logger.warning(f"Invalid payment input: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except PaymentError as e:
        logger.error(f"Payment initialization failed: {str(e)}")
        raise HTTPException(status_code=402, detail=str(e))
    except Exception as e:
        logger.error(f"Payment initialization error: {str(e)}")
        raise HTTPException(status_code=500, detail="Payment initialization failed")


@router.post("/paystack/verify", response_model=PaymentVerifyResponse)
async def verify_paystack_payment(
    verify_data: PaymentVerify,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Verify Paystack payment status."""
    try:
        payment_service = get_payment_service(db)
        result = await payment_service.verify_payment(verify_data.reference)

        if result["status"] == "success":
            user = db.query(User).filter(User.id == user_id).first()
            return PaymentVerifyResponse(
                status="success",
                amount_credited=result.get("metadata", {}).get("namaskah_amount", 0),
                new_balance=user.credits if user else 0,
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
        logger.error(f"Payment verification failed: {str(e)}")
        raise HTTPException(status_code=402, detail=str(e))
    except Exception as e:
        logger.error(f"Payment verification error: {str(e)}")
        raise HTTPException(status_code=500, detail="Payment verification failed")


@router.post("/paystack/webhook")
async def paystack_webhook(request: Request, db: Session = Depends(get_db)):
    """Handle Paystack webhook notifications."""
    try:

        signature = request.headers.get("x-paystack-signature")
        if not signature:
            raise InvalidInputError("Missing signature")

        body = await request.body()
        webhook_service = WebhookService(db)

        if not webhook_service.verify_signature(body, signature):
            raise InvalidInputError("Invalid signature")

        try:
            webhook_data = await request.json()
        except (ValueError, TypeError):
            raise InvalidInputError("Invalid JSON")

        success = webhook_service.process_payment_webhook(webhook_data)
        return {"status": "success" if success else "ignored"}

    except InvalidInputError as e:
        logger.warning(f"Invalid webhook: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Webhook processing failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Webhook processing failed")


@router.get("/transactions", response_model=TransactionHistoryResponse)
def get_transaction_history(
    user_id: str = Depends(get_current_user_id),
    transaction_type: Optional[str] = Query(None),
    limit: int = Query(50, le=100),
    skip: int = Query(0),
    db: Session = Depends(get_db),
):
    """Get user's transaction history."""
    try:
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
    except Exception as e:
        logger.error(f"Failed to get transaction history: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve transactions")


@router.get("/transactions/export")
async def export_transactions(
    user_id: str = Depends(get_current_user_id),
    export_format: str = Query("csv"),
    db: Session = Depends(get_db),
):
    """Export user's transaction history."""
    try:
        if export_format not in ["csv", "json"]:
            raise InvalidInputError("Invalid format. Use 'csv' or 'json'")

        transactions = (
            db.query(Transaction)
            .filter(Transaction.user_id == user_id)
            .order_by(Transaction.created_at.desc())
            .all()
        )

        if export_format == "csv":
            output = io.StringIO()
            writer = csv.writer(output)
            writer.writerow(["Date", "Type", "Amount (N)", "Description"])
            for t in transactions:
                writer.writerow([
                    t.created_at.strftime("%Y-%m-%d %H:%M:%S"),
                    t.type.upper(),
                    f"{t.amount:.2f}",
                    t.description,
                ])
            output.seek(0)
            return StreamingResponse(
                iter([output.getvalue()]),
                media_type="text/csv",
                headers={"Content-Disposition": f"attachment; filename=transactions_{user_id}.csv"},
            )

        else:
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
                headers={"Content-Disposition": f"attachment; filename=transactions_{user_id}.json"},
            )

    except InvalidInputError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Export failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Export failed")


@router.get("/spending-summary")
def get_spending_summary(
    user_id: str = Depends(get_current_user_id),
    days: int = Query(30),
    db: Session = Depends(get_db),
):
    """Get spending summary and analytics."""
    try:
        start_date = datetime.now(timezone.utc) - timedelta(days=days)

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

            daily_spending.append({
                "date": day_start.strftime("%Y-%m-%d"),
                "amount": abs(day_spent)
            })

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

    except Exception as e:
        logger.error(f"Failed to get spending summary: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve summary")
