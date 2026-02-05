"""Payment service for handling Paystack integration."""

import asyncio
import hashlib
import hmac
import json
import requests
from datetime import datetime, timezone
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
from app.core.config import get_settings
from app.core.logging import get_logger
from app.core.cache import get_redis
from app.models.user import User
from app.models.transaction import Transaction, PaymentLog

logger = get_logger(__name__)
settings = get_settings()


class PaymentService:
    """Service for handling payment operations."""

    def __init__(self, db: Session):
        self.db = db

    def _check_idempotency(self, idempotency_key: str) -> Optional[Dict]:
        """Check if operation already processed."""
        existing = self.db.query(PaymentLog).filter(
            PaymentLog.idempotency_key == idempotency_key
        ).first()
        
        if existing and existing.state == 'completed':
            return {
                "payment_id": existing.reference,
                "reference": existing.reference,
                "status": "completed",
                "cached": True
            }
        return None

    async def initialize_payment(self, user_id: str, email: str, amount_usd: float, idempotency_key: str = None) -> Dict[str, Any]:
        """Initialize payment with Paystack."""
        try:
            # Check idempotency
            if idempotency_key:
                cached = self._check_idempotency(idempotency_key)
                if cached:
                    return cached
            
            # Convert USD to kobo (Paystack uses kobo for NGN)
            amount_kobo = int(amount_usd * 100 * 800)  # Rough USD to NGN conversion
            reference = f"namaskah_{user_id}_{int(datetime.now().timestamp())}"
            
            # Create PaymentLog with state='pending'
            payment_log = PaymentLog(
                user_id=user_id,
                email=email,
                reference=reference,
                amount_usd=amount_usd,
                amount_ngn=amount_kobo / 100,
                namaskah_amount=amount_usd,
                state='pending',
                idempotency_key=idempotency_key,
                processing_started_at=datetime.now(timezone.utc)
            )
            self.db.add(payment_log)
            self.db.commit()
            
            payload = {
                "email": email,
                "amount": amount_kobo,
                "currency": "NGN",
                "reference": reference,
                "metadata": {
                    "user_id": user_id,
                    "namaskah_amount": amount_usd
                }
            }

            headers = {
                "Authorization": f"Bearer {settings.paystack_secret_key}",
                "Content-Type": "application/json"
            }

            response = requests.post(
                "https://api.paystack.co/transaction/initialize",
                json=payload,
                headers=headers,
                timeout=30
            )

            if response.status_code == 200:
                data = response.json()
                if data.get("status"):
                    payment_log.state = 'processing'
                    self.db.commit()
                    return {
                        "payment_id": data["data"]["reference"],
                        "authorization_url": data["data"]["authorization_url"],
                        "access_code": data["data"]["access_code"],
                        "reference": data["data"]["reference"]
                    }
            
            payment_log.state = 'failed'
            payment_log.error_message = response.text
            self.db.commit()
            raise Exception(f"Payment initialization failed: {response.text}")

        except Exception as e:
            logger.error(f"Payment initialization error: {e}")
            raise

    async def verify_payment(self, reference: str) -> Dict[str, Any]:
        """Verify payment with Paystack."""
        try:
            headers = {
                "Authorization": f"Bearer {settings.paystack_secret_key}",
                "Content-Type": "application/json"
            }

            response = requests.get(
                f"https://api.paystack.co/transaction/verify/{reference}",
                headers=headers,
                timeout=30
            )

            if response.status_code == 200:
                data = response.json()
                return data
            
            raise Exception(f"Payment verification failed: {response.text}")

        except Exception as e:
            logger.error(f"Payment verification error: {e}")
            raise

    def credit_user(self, user_id: str, amount: float, reference: str) -> bool:
        """Credit user account after successful payment."""
        try:
            # Check if already credited with SELECT FOR UPDATE
            payment_log = self.db.query(PaymentLog).filter(
                PaymentLog.reference == reference
            ).with_for_update().first()
            
            if not payment_log:
                raise ValueError(f"Payment log {reference} not found")
            
            if payment_log.credited:
                logger.warning(f"Payment {reference} already credited")
                return True
            
            # Atomic update with SELECT FOR UPDATE
            user = self.db.query(User).filter(
                User.id == user_id
            ).with_for_update().first()
            
            if not user:
                raise ValueError(f"User {user_id} not found")
            
            # Update in transaction
            user.credits = (user.credits or 0.0) + amount
            payment_log.credited = True
            payment_log.state = 'completed'
            payment_log.processing_completed_at = datetime.now(timezone.utc)
            
            # Create transaction record
            transaction = Transaction(
                user_id=user_id,
                reference=reference,
                payment_log_id=payment_log.id,
                type="credit",
                amount=amount,
                description=f"Payment credit via Paystack - {reference}",
                status="completed"
            )
            
            self.db.add(transaction)
            self.db.commit()
            
            logger.info(f"Credited {amount} to user {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Credit user error: {e}")
            self.db.rollback()
            raise

    def verify_webhook_signature(self, payload: bytes, signature: str) -> bool:
        """Verify Paystack webhook signature."""
        try:
            expected_signature = hmac.new(
                settings.paystack_secret_key.encode('utf-8'),
                payload,
                hashlib.sha512
            ).hexdigest()
            
            return hmac.compare_digest(expected_signature, signature)
        except Exception as e:
            logger.error(f"Webhook signature verification error: {e}")
            return False

    async def credit_user_with_lock(self, user_id: str, amount: float, reference: str) -> bool:
        """Credit user with distributed lock to prevent race conditions."""
        redis = get_redis()
        lock_key = f"payment_lock:{reference}"
        
        # Try to acquire lock (30 second timeout)
        lock = redis.lock(lock_key, timeout=30)
        
        if not lock.acquire(blocking=True, blocking_timeout=10):
            raise Exception(f"Could not acquire payment lock for {reference}")
        
        try:
            return self.credit_user(user_id, amount, reference)
        finally:
            try:
                lock.release()
            except Exception as e:
                logger.warning(f"Lock release error: {e}")

    async def process_webhook_with_retry(self, user_id: str, amount: float, reference: str, max_retries: int = 3) -> bool:
        """Process webhook with retry logic and exponential backoff."""
        for attempt in range(max_retries):
            try:
                return await self.credit_user_with_lock(user_id, amount, reference)
            except Exception as e:
                if attempt == max_retries - 1:
                    # Log to dead letter queue
                    self._log_failed_webhook(user_id, amount, reference, str(e))
                    raise
                
                # Exponential backoff
                wait_time = 2 ** attempt
                logger.warning(f"Webhook retry {attempt + 1}/{max_retries} after {wait_time}s: {e}")
                await asyncio.sleep(wait_time)
    
    def _log_failed_webhook(self, user_id: str, amount: float, reference: str, error: str):
        """Log failed webhook to dead letter queue."""
        try:
            # Update PaymentLog with error
            payment_log = self.db.query(PaymentLog).filter(
                PaymentLog.reference == reference
            ).first()
            
            if payment_log:
                payment_log.state = 'failed'
                payment_log.error_message = f"Webhook processing failed after retries: {error}"
                self.db.commit()
            
            logger.error(f"Dead letter queue: {reference} - {error}")
        except Exception as e:
            logger.error(f"Failed to log dead letter: {e}")


def get_payment_service(db: Session) -> PaymentService:
    """Get payment service instance."""
    return PaymentService(db)
