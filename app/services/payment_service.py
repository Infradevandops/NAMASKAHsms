"""Payment processing service for Paystack integration."""
import hashlib
import hmac
from datetime import datetime, timezone
from typing import Any, Dict, Optional

import httpx
from sqlalchemy.orm import Session

from app.core.config import settings

from .base import BaseService


class PaymentService(BaseService[Transaction]):
    """Service for payment processing with Paystack."""

    def __init__(self, db: Session):
        super().__init__(Transaction, db)
        self.secret_key = settings.paystack_secret_key
        self.client = httpx.AsyncClient(
            headers={"Authorization": f"Bearer {self.secret_key}"}, timeout=30.0
        )

    async def initialize_payment(
        self,
        user_id: str,
        email: str,
        amount_usd: float,
        reference: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Initialize payment with Paystack."""
        if not self.secret_key:
            raise PaymentError("Payment system not configured")

        if amount_usd < 5.0:
            raise ValidationError("Minimum payment amount is $5 USD")

        # Generate reference if not provided
        if not reference:
            timestamp = int(datetime.now(timezone.utc).timestamp())
            reference = f"namaskah_{user_id}_{timestamp}"

        # Convert USD to NGN (get current rate)
        usd_to_ngn_rate = await self._get_exchange_rate()
        amount_ngn = amount_usd * usd_to_ngn_rate
        namaskah_amount = amount_usd * 0.5  # 1 USD = 0.5 Namaskah credits

        payload = {
            "email": email,
            "amount": int(amount_ngn * 100),  # Convert to kobo
            "reference": reference,
            "callback_url": f"{settings.base_url}/app?reference={reference}",
            "metadata": {
                "user_id": user_id,
                "user_email": email,
                "type": "wallet_funding",
                "namaskah_amount": namaskah_amount,
                "usd_amount": amount_usd,
            },
            "channels": ["card", "bank", "ussd", "qr", "mobile_money", "bank_transfer"],
        }

        try:
            response = await self.client.post(
                "https://api.paystack.co/transaction/initialize", json=payload
            )
            response.raise_for_status()

            data = response.json()

            # Log payment initialization
            self._log_payment(
                user_id=user_id,
                email=email,
                reference=reference,
                amount_ngn=amount_ngn,
                amount_usd=amount_usd,
                namaskah_amount=namaskah_amount,
                status="initialized",
            )

            return {
                "success": True,
                "authorization_url": data["data"]["authorization_url"],
                "access_code": data["data"]["access_code"],
                "reference": reference,
                "payment_details": {
                    "namaskah_amount": namaskah_amount,
                    "usd_amount": amount_usd,
                    "ngn_amount": amount_ngn,
                    "exchange_rate": usd_to_ngn_rate,
                },
            }

        except httpx.RequestError as e:
            raise PaymentError(f"Payment gateway error: {str(e)}")
        except (ValueError, KeyError, TypeError) as e:
            raise PaymentError(f"Payment initialization failed: {str(e)}")

    async def verify_payment(self, reference: str) -> Dict[str, Any]:
        """Verify payment with Paystack."""
        if not self.secret_key:
            raise PaymentError("Payment system not configured")

        try:
            response = await self.client.get(
                f"https://api.paystack.co/transaction/verify/{reference}"
            )
            response.raise_for_status()

            data = response.json()

            if not data.get("status"):
                raise PaymentError("Invalid response from Paystack")

            payment_data = data.get("data", {})
            return {
                "status": payment_data.get("status"),
                "amount": payment_data.get("amount", 0) / 100,  # Convert from kobo
                "reference": payment_data.get("reference"),
                "metadata": payment_data.get("metadata", {}),
            }

        except httpx.RequestError as e:
            raise PaymentError(f"Payment verification failed: {str(e)}")

    def verify_webhook_signature(self, payload: bytes, signature: str) -> bool:
        """Verify Paystack webhook signature."""
        if not self.secret_key:
            return False

        expected_signature = hmac.new(
            self.secret_key.encode("utf - 8"), payload, hashlib.sha512
        ).hexdigest()

        return hmac.compare_digest(expected_signature, signature)

    def process_webhook_payment(self, webhook_data: Dict[str, Any]) -> bool:
        """Process successful payment from webhook."""
        event = webhook_data.get("event")
        if event != "charge.success":
            return False

        payment_data = webhook_data.get("data", {})
        reference = payment_data.get("reference")
        amount_kobo = payment_data.get("amount", 0)
        amount_ngn = amount_kobo / 100

        metadata = payment_data.get("metadata", {})
        user_id = metadata.get("user_id")
        namaskah_amount = metadata.get("namaskah_amount", 0)

        if not reference or not user_id:
            return False

        # Check for duplicate transaction
        existing = (
            self.db.query(Transaction)
            .filter(Transaction.description.contains(reference))
            .first()
        )

        if existing:
            return False  # Already processed

        # Find user and add credits
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            return False

        # Create credit transaction
        transaction = Transaction(
            user_id=user_id,
            amount=namaskah_amount,
            type="credit",
            description=f"Paystack payment: {reference} (NGN {amount_ngn})",
        )

        user.credits += namaskah_amount

        self.db.add(transaction)
        self.db.commit()

        # Update payment log
        payment_log = (
            self.db.query(PaymentLog).filter(PaymentLog.reference == reference).first()
        )

        if payment_log:
            payment_log.webhook_received = True
            payment_log.credited = True
            payment_log.status = "completed"
            payment_log.updated_at = datetime.now(timezone.utc)
            self.db.commit()

        return True

    async def process_refund(
        self, transaction_id: str, amount: Optional[float] = None
    ) -> Dict[str, Any]:
        """Process refund through Paystack."""
        if not self.secret_key:
            raise PaymentError("Payment system not configured")

        payload = {"transaction": transaction_id}
        if amount:
            payload["amount"] = int(amount * 100)  # Convert to kobo

        try:
            response = await self.client.post(
                "https://api.paystack.co/refund", json=payload
            )
            response.raise_for_status()

            return response.json()

        except httpx.RequestError as e:
            raise PaymentError(f"Refund processing failed: {str(e)}")

    @staticmethod
    async def _get_exchange_rate() -> float:
        """Get current USD to NGN exchange rate."""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    "https://api.exchangerate - api.com/v4/latest/USD", timeout=5.0
                )
                if response.status_code == 200:
                    rates = response.json().get("rates", {})
                    return rates.get("NGN", 1478.24)  # Fallback rate
        except (httpx.RequestError, ValueError, KeyError):
            pass

        return 1478.24  # Default fallback rate

    def _log_payment(
        self,
        user_id: str,
        email: str,
        reference: str,
        amount_ngn: float,
        amount_usd: float,
        namaskah_amount: float,
        status: str,
        **kwargs,
    ) -> PaymentLog:
        """Log payment attempt."""
        payment_log = PaymentLog(
            user_id=user_id,
            email=email,
            reference=reference,
            amount_ngn=amount_ngn,
            amount_usd=amount_usd,
            namaskah_amount=namaskah_amount,
            status=status,
            payment_method="paystack",
            **kwargs,
        )

        self.db.add(payment_log)
        self.db.commit()
        return payment_log

    async def close(self):
        """Close HTTP client."""
        await self.client.aclose()
