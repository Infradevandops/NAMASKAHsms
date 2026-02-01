"""Payment processing endpoints for Paystack integration."""


import json
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Request
from app.core.pydantic_compat import BaseModel, Field, field_validator
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.dependencies import get_current_user_id
from app.core.logging import get_logger
from app.models.transaction import PaymentLog, Transaction
from app.models.user import User
from app.schemas.payment import CryptoWalletResponse
from app.services.email_service import email_service
from app.services.notification_dispatcher import NotificationDispatcher
from app.services.paystack_service import paystack_service
import asyncio
import asyncio
from app.core.config import settings

logger = get_logger(__name__)
router = APIRouter(prefix="/billing", tags=["Billing"])


# Request Models with Validation

class InitializePaymentRequest(BaseModel):

    """Request model for payment initialization."""

    amount_usd: float = Field(..., gt=0, le=10000, description="Amount in USD")

    @field_validator("amount_usd", mode="before")
    @classmethod
    def validate_amount(cls, v):

        """Validate payment amount."""
        if v < 0.01:
            raise ValueError("Minimum amount is $0.01")
        if v > 10000:
            raise ValueError("Maximum amount is $10,000")
        # Round to 2 decimal places
        return round(v, 2)


        @router.post("/initialize-payment")
    async def initialize_payment(
        request: InitializePaymentRequest,
        user_id: str = Depends(get_current_user_id),
        db: Session = Depends(get_db),
        ):
        """Initialize a payment transaction.

        Args:
        request: Payment initialization request with amount_usd

        Returns:
        Payment initialization details with authorization URL

        Raises:
        400: Invalid amount
        401: Unauthorized
        404: User not found
        503: Payment service unavailable
        500: Internal server error
        """
        try:
        amount_usd = request.amount_usd

        # Get user
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            logger.error(f"User {user_id} not found")
            raise HTTPException(status_code=404, detail="User not found")

        # Check Paystack is configured
        if not paystack_service.enabled:
            logger.error("Paystack not configured")
            raise HTTPException(
                status_code=503,
                detail="Payment service unavailable. Please try again later.",
            )

        # Convert USD to Kobo (1 USD = 1500 NGN, 1 NGN = 100 Kobo)
        amount_ngn = amount_usd * 1500
        amount_kobo = int(amount_ngn * 100)

        # Generate reference
        reference = f"namaskah_{user_id}_{int(datetime.now(timezone.utc).timestamp())}"

        # Initialize payment with Paystack
        logger.info(f"Initializing payment for user {user_id}: ${amount_usd}")

        try:
            result = await paystack_service.initialize_payment(
                email=user.email,
                amount_kobo=amount_kobo,
                reference=reference,
                metadata={
                    "user_id": user_id,
                    "amount_usd": amount_usd,
                    "amount_ngn": amount_ngn,
                },
            )
        except Exception as e:
            logger.error(f"Paystack API error: {str(e)}")
            raise HTTPException(status_code=503, detail="Payment gateway error. Please try again later.")

        # Create payment log
        try:
            payment_log = PaymentLog(
                user_id=user_id,
                email=user.email,
                reference=reference,
                amount_ngn=amount_ngn,
                amount_usd=amount_usd,
                namaskah_amount=amount_usd,
                status="pending",
                payment_method="paystack",
            )
            db.add(payment_log)
            db.commit()

            # CRITICAL: Notify user that payment was initiated
            notification_dispatcher = NotificationDispatcher(db)
            notification_dispatcher.on_payment_initiated(
                user_id=user_id,
                amount=amount_usd,
                reference=reference
            )

        except Exception as e:
            db.rollback()
            logger.error(f"Failed to create payment log: {str(e)}")
            raise HTTPException(status_code=500, detail="Failed to process payment. Please try again.")

        logger.info(f"Payment initialized: Reference={reference}, " f"Amount=${amount_usd}, User={user_id}")

        return {
            "authorization_url": result["authorization_url"],
            "access_code": result["access_code"],
            "reference": reference,
            "amount_usd": amount_usd,
            "amount_ngn": amount_ngn,
            "status": "pending",
        }

        except HTTPException:
        raise
        except ValueError as e:
        logger.warning(f"Validation error: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
        except Exception as e:
        logger.error(f"Unexpected error in payment initialization: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="An unexpected error occurred. Please try again later.",
        )


        @router.get("/verify-payment/{reference}")
    async def verify_payment(
        reference: str,
        user_id: str = Depends(get_current_user_id),
        db: Session = Depends(get_db),
        ):
        """Verify a payment transaction.

        Args:
        reference: Payment reference to verify

        Returns:
        Payment verification details

        Raises:
        400: Invalid reference format
        401: Unauthorized
        404: Payment not found
        503: Payment service unavailable
        500: Internal server error
        """
        try:
        # Validate reference format
        if not reference or len(reference) < 5:
            raise HTTPException(status_code=400, detail="Invalid payment reference")

        # Get payment log
        payment_log = (
            db.query(PaymentLog)
            .filter(
                PaymentLog.reference == reference,
                PaymentLog.user_id == user_id,
            )
            .first()
        )

        if not payment_log:
            logger.warning(f"Payment log not found: {reference} for user {user_id}")
            raise HTTPException(status_code=404, detail="Payment not found")

        # Verify with Paystack
        logger.info(f"Verifying payment: {reference}")

        try:
            result = await paystack_service.verify_payment(reference)
        except Exception as e:
            logger.error(f"Paystack verification error: {str(e)}")
            raise HTTPException(status_code=503, detail="Payment verification service unavailable")

        # Update payment log
        payment_log.status = result["status"]
        payment_log.webhook_received = True

        # If payment successful, add credits (idempotent)
        if result["status"] == "success" and not payment_log.credited:
            user = db.query(User).filter(User.id == user_id).first()
        if user:
        try:
                    # Add credits
                    credits_to_add = payment_log.namaskah_amount
                    user.credits = (user.credits or 0.0) + credits_to_add

                    # Create transaction record
                    transaction = Transaction(
                        user_id=user_id,
                        amount=credits_to_add,
                        type="credit",
                        description=f"Payment via Paystack (Ref: {reference})",
                    )
                    db.add(transaction)

                    payment_log.credited = True
                    logger.info(
                        f"Credits added: User={user_id}, Amount={credits_to_add}, " f"New Balance={user.credits}"
                    )
        except Exception as e:
                    db.rollback()
                    logger.error(f"Error adding credits: {str(e)}")
                    raise HTTPException(status_code=500, detail="Failed to add credits")

        db.commit()

        return {
            "reference": reference,
            "status": result["status"],
            "amount": result["amount"],
            "paid_at": result.get("paid_at"),
            "credited": payment_log.credited,
            "amount_usd": payment_log.amount_usd,
            "amount_ngn": payment_log.amount_ngn,
        }

        except HTTPException:
        raise
        except ValueError as e:
        logger.warning(f"Validation error: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
        except Exception as e:
        logger.error(f"Unexpected error in payment verification: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="An unexpected error occurred")


        @router.post("/webhook")
    async def paystack_webhook(
        request: Request,
        db: Session = Depends(get_db),
        ):
        """Handle Paystack webhook events.

        Paystack sends webhook events for payment status changes.
        Signature verification is required for security.
        """
        webhook_id = None

        try:
        # Get raw body for signature verification
        body = await request.body()

        # Get signature from header
        signature = request.headers.get("x-paystack-signature", "")

        if not signature:
            logger.warning("Webhook received without signature header")
            raise HTTPException(status_code=401, detail="Missing signature")

        # Verify signature
        if not paystack_service.verify_webhook_signature(body, signature):
            logger.warning("Invalid webhook signature received")
            raise HTTPException(status_code=401, detail="Invalid signature")

        # Parse JSON
        try:
            data = json.loads(body)
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in webhook: {str(e)}")
            raise HTTPException(status_code=400, detail="Invalid JSON")

        event = data.get("event")
        payload = data.get("data", {})
        webhook_id = payload.get("id")

        logger.info(f"Webhook received: Event={event}, ID={webhook_id}")

        # Handle charge.success event
        if event == "charge.success":
            reference = payload.get("reference")
            amount = payload.get("amount")

            logger.info(f"Charge success: Reference={reference}, Amount={amount}")

            # Get payment log
            payment_log = db.query(PaymentLog).filter(PaymentLog.reference == reference).first()

        if not payment_log:
                logger.warning(f"Payment log not found for reference: {reference}")
        return {"status": "ok", "message": "Payment not found"}

            # Check if already credited (idempotent)
        if payment_log.credited:
                logger.info(f"Payment already credited: {reference}")
        return {"status": "ok", "message": "Already processed"}

            # Get user
            user = db.query(User).filter(User.id == payment_log.user_id).first()
        if not user:
                logger.error(f"User not found: {payment_log.user_id}")
        return {"status": "error", "message": "User not found"}

        try:
                # Add credits
                credits_to_add = payment_log.namaskah_amount
                user.credits = (user.credits or 0.0) + credits_to_add

                # Create transaction record
                transaction = Transaction(
                    user_id=payment_log.user_id,
                    amount=credits_to_add,
                    type="credit",
                    description=f"Payment via Paystack (Ref: {reference})",
                )
                db.add(transaction)

                # Update payment log
                payment_log.status = "success"
                payment_log.credited = True
                payment_log.webhook_received = True

                db.commit()

                logger.info(
                    f"Credits added via webhook: User={payment_log.user_id}, "
                    f"Amount={credits_to_add}, New Balance={user.credits}"
                )

                # Send email receipt (async, don't block webhook)
        try:

                    asyncio.create_task(
                        email_service.send_payment_receipt(
                            user_email=user.email,
                            payment_details={
                                "reference": reference,
                                "amount_usd": payment_log.amount_usd,
                                "credits_added": credits_to_add,
                                "new_balance": user.credits,
                                "timestamp": datetime.now(timezone.utc).isoformat(),
                            },
                        )
                    )
        except Exception as e:
                    logger.warning(f"Failed to send receipt email: {str(e)}")

                # CRITICAL: Create in-app notification using dispatcher
        try:
                    notification_dispatcher = NotificationDispatcher(db)
                    notification_dispatcher.on_payment_completed(
                        user_id=payment_log.user_id,
                        amount=payment_log.amount_usd,
                        credits_added=credits_to_add,
                        reference=reference,
                        new_balance=user.credits
                    )
        except Exception as e:
                    logger.warning(f"Failed to create notification: {str(e)}")

        except Exception as e:
                db.rollback()
                logger.error(f"Error processing successful payment: {str(e)}", exc_info=True)
        return {"status": "error", "message": str(e)}

        # Handle charge.failed event
        elif event == "charge.failed":
            reference = payload.get("reference")
            reason = payload.get("gateway_response", "Unknown reason")

            logger.warning(f"Charge failed: Reference={reference}, Reason={reason}")

        try:
                payment_log = db.query(PaymentLog).filter(PaymentLog.reference == reference).first()

        if payment_log:
                    payment_log.status = "failed"
                    payment_log.webhook_received = True
                    payment_log.error_message = reason
                    db.commit()
                    logger.info(f"Payment marked as failed: {reference}")

                    # Get user for notifications
                    user = db.query(User).filter(User.id == payment_log.user_id).first()
        if user:
                        # Send failed payment email (async, don't block webhook)
        try:

                            asyncio.create_task(
                                email_service.send_payment_failed_alert(
                                    user_email=user.email,
                                    payment_details={
                                        "reference": reference,
                                        "amount_usd": payment_log.amount_usd,
                                        "reason": reason,
                                        "timestamp": datetime.now(timezone.utc).isoformat(),
                                    },
                                )
                            )
        except Exception as e:
                            logger.warning(f"Failed to send failed payment email: {str(e)}")

                        # Create in-app notification
        try:
                            notification_dispatcher = NotificationDispatcher(db)
                            notification_dispatcher.on_payment_failed(
                                user_id=payment_log.user_id,
                                amount=payment_log.amount_usd,
                                reason=reason,
                                reference=reference
                            )
        except Exception as e:
                            logger.warning(f"Failed to create notification: {str(e)}")
        except Exception as e:
                db.rollback()
                logger.error(f"Error processing failed payment: {str(e)}", exc_info=True)
        return {"status": "error", "message": str(e)}

        else:
            logger.info(f"Unhandled webhook event: {event}")

        return {"status": "ok"}

        except HTTPException:
        raise
        except Exception as e:
        logger.error(f"Webhook processing error: {str(e)}", exc_info=True)
        # Return 200 to prevent Paystack from retrying
        # Log the error for manual investigation
        return {"status": "error", "message": str(e)}


        @router.get("/transactions")
    async def get_transactions(
        user_id: str = Depends(get_current_user_id),
        skip: int = 0,
        limit: int = 10,
        db: Session = Depends(get_db),
        ):
        """Get user's transaction history.

        Args:
        skip: Number of records to skip (pagination)
        limit: Number of records to return (max 100)

        Returns:
        List of transactions with pagination metadata

        Raises:
        400: Invalid pagination parameters
        401: Unauthorized
        500: Internal server error
        """
        try:
        # Validate pagination parameters
        if skip < 0:
            raise HTTPException(status_code=400, detail="skip must be non-negative")

        if limit < 1 or limit > 100:
            raise HTTPException(status_code=400, detail="limit must be between 1 and 100")

        # Verify user exists
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        # Get total count
        total = db.query(Transaction).filter(Transaction.user_id == user_id).count()

        # Get transactions
        transactions = (
            db.query(Transaction)
            .filter(Transaction.user_id == user_id)
            .order_by(Transaction.created_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )

        logger.info(
            f"Retrieved {len(transactions)} transactions for user {user_id} "
            f"(total: {total}, skip: {skip}, limit: {limit})"
        )

        return {
            "total": total,
            "skip": skip,
            "limit": limit,
            "transactions": [
                {
                    "id": t.id,
                    "amount": float(t.amount),
                    "type": t.type,
                    "description": t.description,
                    "created_at": t.created_at.isoformat() if t.created_at else None,
                }
        for t in transactions
            ],
        }

        except HTTPException:
        raise
        except Exception as e:
        logger.error(f"Failed to get transactions: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to retrieve transactions")


        @router.get("/balance")
    async def get_balance(
        user_id: str = Depends(get_current_user_id),
        db: Session = Depends(get_db),
        ):
        """Get user's current credit balance.

        Returns:
        User's credit balance and metadata

        Raises:
        401: Unauthorized
        404: User not found
        500: Internal server error
        """
        try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            logger.warning(f"User not found: {user_id}")
            raise HTTPException(status_code=404, detail="User not found")

        balance = float(user.credits or 0.0)
        logger.info(f"Retrieved balance for user {user_id}: ${balance}")

        return {
            "user_id": user_id,
            "credits": balance,
            "currency": "USD",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

        except HTTPException:
        raise
        except Exception as e:
        logger.error(f"Failed to get balance: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to retrieve balance")


        @router.get("/crypto-addresses", response_model=CryptoWalletResponse)
    def get_crypto_addresses():

        """Get configured crypto wallet addresses."""

    # Create a simple response without pulling from app.schemas if imports are messy,
    # but we are trying to use the schema we just added.
    # We need to import the schema first.
        return CryptoWalletResponse(
        btc_address=settings.crypto_btc_address,
        eth_address=settings.crypto_eth_address,
        sol_address=settings.crypto_sol_address,
        ltc_address=settings.crypto_ltc_address,
        )
