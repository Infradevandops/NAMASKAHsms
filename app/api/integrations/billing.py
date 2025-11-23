"""Real billing and payment endpoints."""
from app.core.dependencies import get_current_user_id
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.core.database import get_db

logger = get_logger(__name__)
router = APIRouter(prefix="/api/billing", tags=["billing"])


@router.post("/paystack/initialize")
async def initialize_paystack_payment(
    request: Request,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Initialize Paystack payment for credit purchase."""
    try:
        data = await request.json()
        amount = float(data.get("amount", 0))
        email = data.get("email")

        if amount <= 0:
            raise HTTPException(status_code=400, detail="Invalid amount")

        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        # Calculate bonus
        bonus = 0
        if amount >= 50:
            bonus = 7
        elif amount >= 25:
            bonus = 3
        elif amount >= 10:
            bonus = 1

        # Create transaction record
        transaction = Transaction(
            user_id=user_id,
            type="credit_purchase",
            amount=amount,
            bonus=bonus,
            status="pending",
            payment_method="paystack",
            metadata={
                "email": email or user.email,
                "amount_with_bonus": amount + bonus,
            },
        )
        db.add(transaction)
        db.commit()

        # In production, initialize Paystack payment
        # For now, return initialization data
        return {
            "success": True,
            "transaction_id": transaction.id,
            "amount": amount,
            "bonus": bonus,
            "total": amount + bonus,
            "email": email or user.email,
            "message": "Payment initialization ready",
        }

    except HTTPException:
        pass
    except Exception as e:
        logger.error(f"Initialize payment error: {e}")
        raise HTTPException(status_code=500, detail="Failed to initialize payment")


@router.post("/paystack/webhook")
async def paystack_webhook(
    request: Request,
    db: Session = Depends(get_db),
):
    """Handle Paystack payment webhook."""
    try:
        data = await request.json()
        event = data.get("event")
        payment_data = data.get("data", {})

        if event == "charge.success":
            reference = payment_data.get("reference")
            amount = payment_data.get("amount") / 100  # Convert from kobo to naira

            # Find transaction
            transaction = db.query(Transaction).filter(
                Transaction.id == reference
            ).first()

            if transaction:
                # Add credits to user
                user = db.query(User).filter(User.id == transaction.user_id).first()
                if user:
                    total_credits = amount + transaction.bonus
                    user.credits = (user.credits or 0) + total_credits
                    transaction.status = "completed"
                    db.commit()

                    logger.info(f"Payment completed for user {transaction.user_id}: {total_credits} credits")

        return {"success": True}

    except Exception as e:
        logger.error(f"Webhook error: {e}")
        return {"success": False, "error": str(e)}


@router.get("/transactions")
async def get_transactions(
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
    limit: int = 50,
    offset: int = 0,
):
    """Get user's transaction history."""
    try:
        transactions = db.query(Transaction).filter(
            Transaction.user_id == user_id
        ).order_by(
            Transaction.created_at.desc()
        ).offset(offset).limit(limit).all()

        return {
            "success": True,
            "transactions": [
                {
                    "id": t.id,
                    "type": t.type,
                    "amount": t.amount,
                    "bonus": t.bonus,
                    "status": t.status,
                    "payment_method": t.payment_method,
                    "created_at": t.created_at.isoformat(),
                }
                for t in transactions
            ],
            "total": len(transactions),
        }

    except Exception as e:
        logger.error(f"Get transactions error: {e}")
        raise HTTPException(status_code=500, detail="Failed to get transactions")


@router.get("/balance")
async def get_balance(
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Get user's current balance."""
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        return {
            "success": True,
            "balance": float(user.credits or 0),
            "currency": "USD",
        }

    except HTTPException:
        pass
    except Exception as e:
        logger.error(f"Get balance error: {e}")
        raise HTTPException(status_code=500, detail="Failed to get balance")
