"""Payment service for managing payments and credits."""

from datetime import datetime, timezone
from typing import Any, Dict, Optional

from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.core.logging import get_logger
from app.models.transaction import PaymentLog, Transaction
from app.models.user import User
from app.services.credit_service import CreditService
from app.services.paystack_service import paystack_service
from redis import Redis
from redis.lock import Lock
from app.core.config import get_settings
from prometheus_client import Counter, Histogram

logger = get_logger(__name__)

# Metrics
payment_credits = Counter('payment_credits_total', 'Total payment credits')
payment_duplicates = Counter('payment_duplicates_total', 'Duplicate payment attempts')
payment_duration = Histogram('payment_duration_seconds', 'Payment processing time')
webhook_deliveries = Counter('webhook_deliveries_total', 'Webhook deliveries', ['status'])


class PaymentService:
    """Service for managing payments and payment processing."""

    def __init__(self, db: Session, redis: Redis = None):
        """Initialize payment service with database session."""
        self.db = db
        self.credit_service = CreditService(db)
        self.redis = redis or Redis.from_url(get_settings().redis_url)

    async def credit_user(self, reference: str, amount: float, user_id: str) -> Dict[str, Any]:
        """Credit user with idempotency guarantee."""
        # Check if already credited
        idempotency_key = f"payment:credited:{reference}"
        if self.redis.get(idempotency_key):
            logger.warning(f"Payment {reference} already credited")
            payment_duplicates.inc()
            return {"status": "duplicate", "reference": reference}
        
        # Acquire distributed lock
        lock_key = f"payment:lock:{reference}"
        lock = Lock(self.redis, lock_key, timeout=10, blocking_timeout=5)
        
        if not lock.acquire(blocking=True):
            raise ValueError("Could not acquire payment lock")
            
        with payment_duration.time():
            try:
                # Use SELECT FOR UPDATE to prevent race conditions
                user = (
                    self.db.query(User)
                    .filter(User.id == user_id)
                    .with_for_update()
                    .first()
                )
                
                if not user:
                    raise ValueError(f"User {user_id} not found")
                
                # Credit user
                user.credits = (user.credits or 0.0) + amount
                
                # Mark as credited (24 hour TTL)
                self.redis.setex(idempotency_key, 86400, "1")
                
                # Create transaction
                transaction = Transaction(
                    user_id=user_id,
                    amount=amount,
                    type="credit",
                    description=f"Payment {reference}",
                )
                self.db.add(transaction)
                self.db.commit()
                
                logger.info(f"Credited {amount} to user {user_id} (ref: {reference})")
                payment_credits.inc()
                return {"status": "success", "amount": amount, "new_balance": user.credits}
                
            finally:
                lock.release()

    async def initiate_payment(
        self, user_id: str, amount_usd: float, description: str = "Credit purchase"
    ) -> Dict[str, Any]:
        """Initiate a payment transaction.

        Args:
            user_id: User ID
            amount_usd: Amount in USD
            description: Payment description

        Returns:
            Dictionary with payment details and authorization URL

        Raises:
            ValueError: If amount invalid or user not found
        """
        # Validate amount
        if amount_usd <= 0:
            raise ValueError("Amount must be positive")
        
        # Maximum amount check (prevent fraud)
        if amount_usd > 100000:
            raise ValueError("Amount exceeds maximum allowed (100,000 USD)")

        # Get user
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            raise ValueError(f"User {user_id} not found")

        # Check Paystack is configured
        if not paystack_service.enabled:
            raise ValueError("Payment service not available")

        # Convert USD to NGN (1 USD = 1500 NGN)
        amount_ngn = amount_usd * 1500
        amount_kobo = int(amount_ngn * 100)

        # Generate reference
        reference = f"namaskah_{user_id}_{int(datetime.now(timezone.utc).timestamp())}"

        logger.info(f"Initiating payment for user {user_id}: ${amount_usd}")

        try:
            # Initialize payment with Paystack
            result = await paystack_service.initialize_payment(
                email=user.email,
                amount_kobo=amount_kobo,
                reference=reference,
                metadata={
                    "user_id": user_id,
                    "amount_usd": amount_usd,
                    "amount_ngn": amount_ngn,
                    "description": description,
                },
            )

            # Create payment log
            payment_log = PaymentLog(
                user_id=user_id,
                email=user.email,
                reference=reference,
                amount_ngn=amount_ngn,
                amount_usd=amount_usd,
                namaskah_amount=amount_usd,  # 1:1 conversion
                status="pending",
                payment_method="paystack",
            )

            self.db.add(payment_log)
            self.db.commit()

            logger.info(
                f"Payment initiated: Reference={reference}, "
                f"Amount=${amount_usd}, URL={result['authorization_url']}"
            )

            return {
                "reference": reference,
                "authorization_url": result["authorization_url"],
                "access_code": result["access_code"],
                "amount_usd": amount_usd,
                "amount_ngn": amount_ngn,
                "status": "pending",
                "created_at": datetime.now(timezone.utc).isoformat(),
            }

        except Exception as e:
            logger.error(f"Failed to initiate payment: {str(e)}")
            raise ValueError(f"Payment initialization failed: {str(e)}")

    async def verify_payment(self, reference: str, user_id: str) -> Dict[str, Any]:
        """Verify a payment transaction.

        Args:
            reference: Payment reference
            user_id: User ID

        Returns:
            Dictionary with payment verification details

        Raises:
            ValueError: If payment not found or verification fails
        """
        # Get payment log
        payment_log = (
            self.db.query(PaymentLog)
            .filter(PaymentLog.reference == reference, PaymentLog.user_id == user_id)
            .first()
        )

        if not payment_log:
            raise ValueError(f"Payment not found: {reference}")

        logger.info(f"Verifying payment: {reference}")

        try:
            # Verify with Paystack
            result = await paystack_service.verify_payment(reference)

            # Update payment log
            payment_log.status = result["status"]
            payment_log.webhook_received = True

            # If payment successful, add credits
            if result["status"] == "success" and not payment_log.credited:
                user = self.db.query(User).filter(User.id == user_id).first()
                if user:
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

                    self.db.add(transaction)
                    payment_log.credited = True

                    logger.info(
                        f"Credits added: User={user_id}, Amount={credits_to_add}, "
                        f"New Balance={user.credits}"
                    )

            self.db.commit()

            return {
                "reference": reference,
                "status": result["status"],
                "amount_usd": payment_log.amount_usd,
                "amount_ngn": payment_log.amount_ngn,
                "credited": payment_log.credited,
                "paid_at": result.get("paid_at"),
                "verified_at": datetime.now(timezone.utc).isoformat(),
            }

        except Exception as e:
            logger.error(f"Failed to verify payment: {str(e)}")
            raise ValueError(f"Payment verification failed: {str(e)}")

    async def process_webhook(self, event: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Process Paystack webhook event.

        Args:
            event: Event type (charge.success, charge.failed, etc)
            payload: Event payload

        Returns:
            Dictionary with processing result
        """
        logger.info(f"Processing webhook: Event={event}")

        try:
            if event == "charge.success":
                return await self._handle_charge_success(payload)
            elif event == "charge.failed":
                return self._handle_charge_failed(payload)
            else:
                logger.warning(f"Unknown event: {event}")
                return {"status": "ignored", "message": f"Unknown event: {event}"}

        except Exception as e:
            logger.error(f"Webhook processing error: {str(e)}")
            return {"status": "error", "message": str(e)}

    async def _handle_charge_success(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Handle charge.success webhook event.

        Args:
            payload: Event payload

        Returns:
            Dictionary with processing result
        """
        reference = payload.get("reference")
        
        logger.info(f"Charge success: Reference={reference}")

        # Get payment log
        payment_log = (
            self.db.query(PaymentLog).filter(PaymentLog.reference == reference).first()
        )

        if not payment_log:
            logger.warning(f"Payment log not found: {reference}")
            webhook_deliveries.labels(status="ignored").inc()
            return {"status": "ignored", "message": "Payment not found"}

        # Use idempotent credit function
        try:
            result = await self.credit_user(
                reference=reference,
                amount=payment_log.namaskah_amount,
                user_id=payment_log.user_id
            )
            
            # Update payment log
            payment_log.status = "success"
            payment_log.credited = True
            payment_log.webhook_received = True
            self.db.commit()
            
            webhook_deliveries.labels(status="success").inc()
            return result
            
        except Exception as e:
            logger.error(f"Failed to credit user: {str(e)}")
            webhook_deliveries.labels(status="error").inc()
            return {"status": "error", "message": str(e)}

    def _handle_charge_failed(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Handle charge.failed webhook event.

        Args:
            payload: Event payload

        Returns:
            Dictionary with processing result
        """
        reference = payload.get("reference")
        logger.warning(f"Charge failed: Reference={reference}")

        # Get payment log
        payment_log = (
            self.db.query(PaymentLog).filter(PaymentLog.reference == reference).first()
        )

        if payment_log:
            payment_log.status = "failed"
            payment_log.webhook_received = True
            self.db.commit()

        return {"status": "success", "message": "Payment failure recorded"}

    def get_payment_history(
        self, user_id: str, status: Optional[str] = None, skip: int = 0, limit: int = 20
    ) -> Dict[str, Any]:
        """Get payment history for user.

        Args:
            user_id: User ID
            status: Filter by status (pending, success, failed)
            skip: Number of records to skip
            limit: Number of records to return

        Returns:
            Dictionary with payment history
        """
        # Validate user exists
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            raise ValueError(f"User {user_id} not found")

        # Build query
        query = self.db.query(PaymentLog).filter(PaymentLog.user_id == user_id)

        # Apply status filter
        if status:
            query = query.filter(PaymentLog.status == status)

        # Get total count
        total = query.count()

        # Apply pagination and sorting
        payments = (
            query.order_by(desc(PaymentLog.created_at))
            .offset(skip)
            .limit(min(limit, 100))
            .all()
        )

        logger.info(
            f"Retrieved {len(payments)} payments for user {user_id} "
            f"(total: {total}, skip: {skip}, limit: {limit})"
        )

        return {
            "user_id": user_id,
            "total": total,
            "skip": skip,
            "limit": limit,
            "payments": [
                {
                    "reference": p.reference,
                    "amount_usd": p.amount_usd,
                    "amount_ngn": p.amount_ngn,
                    "status": p.status,
                    "credited": p.credited,
                    "payment_method": p.payment_method,
                    "created_at": p.created_at.isoformat() if p.created_at else None,
                    "webhook_received": p.webhook_received,
                }
                for p in payments
            ],
        }

    def get_payment_summary(self, user_id: str) -> Dict[str, Any]:
        """Get payment summary for user.

        Args:
            user_id: User ID

        Returns:
            Dictionary with payment summary
        """
        # Validate user exists
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            raise ValueError(f"User {user_id} not found")

        # Get all payments
        payments = self.db.query(PaymentLog).filter(PaymentLog.user_id == user_id).all()

        # Calculate totals
        total_paid = 0.0
        total_credited = 0.0
        successful_payments = 0
        failed_payments = 0
        pending_payments = 0

        for p in payments:
            if p.status == "success":
                total_paid += p.amount_usd
                successful_payments += 1
                if p.credited:
                    total_credited += p.amount_usd
            elif p.status == "failed":
                failed_payments += 1
            elif p.status == "pending":
                pending_payments += 1

        logger.info(f"Generated payment summary for user {user_id}")

        return {
            "user_id": user_id,
            "current_balance": float(user.credits or 0.0),
            "total_paid": total_paid,
            "total_credited": total_credited,
            "successful_payments": successful_payments,
            "failed_payments": failed_payments,
            "pending_payments": pending_payments,
            "total_payments": len(payments),
        }

    def refund_payment(
        self, reference: str, user_id: str, reason: str = "User requested refund"
    ) -> Dict[str, Any]:
        """Refund a payment (admin only).

        Args:
            reference: Payment reference
            user_id: User ID
            reason: Refund reason

        Returns:
            Dictionary with refund details

        Raises:
            ValueError: If payment not found or cannot be refunded
        """
        # Get payment log
        payment_log = (
            self.db.query(PaymentLog)
            .filter(PaymentLog.reference == reference, PaymentLog.user_id == user_id)
            .first()
        )

        if not payment_log:
            raise ValueError(f"Payment not found: {reference}")

        if payment_log.status != "success":
            raise ValueError(f"Cannot refund payment with status: {payment_log.status}")

        # Get user
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            raise ValueError(f"User {user_id} not found")

        # Deduct credits
        credits_to_deduct = payment_log.namaskah_amount
        if (user.credits or 0.0) < credits_to_deduct:
            raise ValueError("Insufficient credits to refund")

        user.credits = (user.credits or 0.0) - credits_to_deduct

        # Create refund transaction
        transaction = Transaction(
            user_id=user_id,
            amount=-credits_to_deduct,
            type="refund",
            description=f"Refund for payment {reference}: {reason}",
        )

        self.db.add(transaction)

        # Update payment log
        payment_log.status = "refunded"
        payment_log.credited = False

        self.db.commit()

        logger.warning(
            f"Payment refunded: Reference={reference}, User={user_id}, "
            f"Amount={credits_to_deduct}, Reason={reason}"
        )

        return {
            "reference": reference,
            "status": "refunded",
            "amount_refunded": credits_to_deduct,
            "new_balance": float(user.credits),
            "reason": reason,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
