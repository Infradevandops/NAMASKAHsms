"""Webhook verification and processing service."""
import hashlib
import hmac
from typing import Any, Dict

from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.payment import PaymentLog
from app.models.transaction import Transaction
from app.models.user import User


class WebhookService:
    """Handle Paystack webhook verification and processing."""

    def __init__(self, db: Session):
        self.db = db
        self.secret = settings.paystack_secret_key

    def verify_signature(self, payload: bytes, signature: str) -> bool:
        """Verify Paystack webhook signature."""
        if not self.secret:
            return False

        expected_signature = hmac.new(
            self.secret.encode("utf-8"), payload, hashlib.sha512
        ).hexdigest()

        return hmac.compare_digest(signature, expected_signature)

    def process_payment_webhook(self, webhook_data: Dict[str, Any]) -> bool:
        """Process successful payment webhook."""
        event = webhook_data.get("event")
        data = webhook_data.get("data", {})

        if event != "charge.success":
            return False

        reference = data.get("reference")
        if not reference:
            return False

        # Find payment log
        payment_log = (
            self.db.query(PaymentLog).filter(PaymentLog.reference == reference).first()
        )

        if not payment_log or payment_log.credited:
            return False

        # Verify payment amount matches
        paid_amount = data.get("amount", 0) / 100  # Paystack returns in kobo
        if abs(paid_amount - payment_log.amount_ngn) > 1:  # Allow 1 NGN difference
            return False

        # Credit user account
        user = self.db.query(User).filter(User.id == payment_log.user_id).first()
        if not user:
            return False

        # Add credits to user
        user.credits += payment_log.namaskah_amount

        # Create transaction record
        transaction = Transaction(
            user_id=user.id,
            amount=payment_log.namaskah_amount,
            type="credit",
            description=f"Payment via Paystack - {reference}",
        )
        self.db.add(transaction)

        # Update payment log
        payment_log.status = "completed"
        payment_log.webhook_received = True
        payment_log.credited = True

        self.db.commit()
        return True
