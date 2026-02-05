"""Payment service for handling Paystack integration."""

import hashlib
import hmac
import json
import requests
from datetime import datetime, timezone
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
from app.core.config import get_settings
from app.core.logging import get_logger
from app.models.user import User
from app.models.transaction import Transaction

logger = get_logger(__name__)
settings = get_settings()


class PaymentService:
    """Service for handling payment operations."""

    def __init__(self, db: Session):
        self.db = db

    async def initialize_payment(self, user_id: str, email: str, amount_usd: float) -> Dict[str, Any]:
        """Initialize payment with Paystack."""
        try:
            # Convert USD to kobo (Paystack uses kobo for NGN)
            amount_kobo = int(amount_usd * 100 * 800)  # Rough USD to NGN conversion
            
            payload = {
                "email": email,
                "amount": amount_kobo,
                "currency": "NGN",
                "reference": f"namaskah_{user_id}_{int(datetime.now().timestamp())}",
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
        return {
                        "payment_id": data["data"]["reference"],
                        "authorization_url": data["data"]["authorization_url"],
                        "access_code": data["data"]["access_code"],
                        "reference": data["data"]["reference"]
                    }
            
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
            user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
                raise ValueError(f"User {user_id} not found")

            # Credit user
            user.credits = (user.credits or 0.0) + amount

            # Create transaction record
            transaction = Transaction(
                user_id=user_id,
                type="credit",
                amount=amount,
                description=f"Payment credit via Paystack - {reference}",
                status="completed",
                reference=reference,
                created_at=datetime.now(timezone.utc)
            )

            self.db.add(transaction)
            self.db.commit()
            
            logger.info(f"Credited {amount} to user {user_id}")
        return True

        except Exception as e:
            logger.error(f"Credit user error: {e}")
            self.db.rollback()
        return False

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


    def get_payment_service(db: Session) -> PaymentService:
        """Get payment service instance."""
        return PaymentService(db)
