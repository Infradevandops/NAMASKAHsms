"""Paystack payment service for handling payments and webhooks."""


import hashlib
import hmac
from typing import Any, Dict, Optional
import httpx
from app.core.config import get_settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class PaystackService:

    """Service for Paystack payment processing."""

    def __init__(self):

        settings = get_settings()
        self.secret_key = settings.paystack_secret_key
        self.public_key = settings.paystack_public_key
        self.base_url = "https://api.paystack.co"
        self.enabled = bool(self.secret_key and self.public_key)

        if self.enabled:
            logger.info("Paystack service initialized")
        else:
            logger.warning("Paystack not configured")

    async def initialize_payment(
        self,
        email: str,
        amount_kobo: int,
        reference: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        ) -> Dict[str, Any]:
        """Initialize a payment transaction.

        Args:
            email: Customer email
            amount_kobo: Amount in kobo (1 naira = 100 kobo)
            reference: Unique reference for the transaction
            metadata: Additional metadata to store with transaction

        Returns:
            Dictionary with authorization_url and access_code
        """
        if not self.enabled:
            raise Exception("Paystack not configured")

        try:
            async with httpx.AsyncClient() as client:
                payload = {
                    "email": email,
                    "amount": amount_kobo,
                }

        if reference:
                    payload["reference"] = reference

        if metadata:
                    payload["metadata"] = metadata

                response = await client.post(
                    f"{self.base_url}/transaction/initialize",
                    headers=self._get_headers(),
                    json=payload,
                    timeout=10.0,
                )
                response.raise_for_status()
                data = response.json()

        if not data.get("status"):
                    raise Exception(f"Paystack error: {data.get('message')}")

                result = data.get("data", {})
                logger.info(
                    f"Payment initialized for {email}: " f"Amount={amount_kobo}, Reference={result.get('reference')}"
                )

        return {
                    "authorization_url": result.get("authorization_url"),
                    "access_code": result.get("access_code"),
                    "reference": result.get("reference"),
                }

        except Exception as e:
            logger.error(f"Failed to initialize payment: {str(e)}")
            raise

    async def verify_payment(self, reference: str) -> Dict[str, Any]:
        """Verify a payment transaction.

        Args:
            reference: Transaction reference to verify

        Returns:
            Dictionary with payment details
        """
        if not self.enabled:
            raise Exception("Paystack not configured")

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/transaction/verify/{reference}",
                    headers=self._get_headers(),
                    timeout=10.0,
                )
                response.raise_for_status()
                data = response.json()

        if not data.get("status"):
                    raise Exception(f"Paystack error: {data.get('message')}")

                result = data.get("data", {})
                logger.info(
                    f"Payment verified: Reference={reference}, "
                    f"Status={result.get('status')}, Amount={result.get('amount')}"
                )

        return {
                    "status": result.get("status"),
                    "reference": result.get("reference"),
                    "amount": result.get("amount"),
                    "paid_at": result.get("paid_at"),
                    "customer": result.get("customer", {}),
                    "authorization": result.get("authorization", {}),
                }

        except Exception as e:
            logger.error(f"Failed to verify payment: {str(e)}")
            raise

    def verify_webhook_signature(self, payload: bytes, signature: str) -> bool:

        """Verify webhook signature from Paystack.

        Args:
            payload: Raw request body
            signature: X-Paystack-Signature header value

        Returns:
            True if signature is valid, False otherwise
        """
        try:
            hash_object = hmac.new(
                self.secret_key.encode(),
                payload,
                hashlib.sha512,
            )
            computed_signature = hash_object.hexdigest()
        return computed_signature == signature
        except Exception as e:
            logger.error(f"Webhook signature verification failed: {str(e)}")
        return False

    async def get_transaction(self, transaction_id: int) -> Dict[str, Any]:
        """Get transaction details by ID.

        Args:
            transaction_id: Paystack transaction ID

        Returns:
            Dictionary with transaction details
        """
        if not self.enabled:
            raise Exception("Paystack not configured")

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/transaction/{transaction_id}",
                    headers=self._get_headers(),
                    timeout=10.0,
                )
                response.raise_for_status()
                data = response.json()

        if not data.get("status"):
                    raise Exception(f"Paystack error: {data.get('message')}")

        return data.get("data", {})

        except Exception as e:
            logger.error(f"Failed to get transaction: {str(e)}")
            raise

    async def get_balance(self) -> Dict[str, Any]:
        """Get account balance.

        Returns:
            Dictionary with balance information
        """
        if not self.enabled:
            raise Exception("Paystack not configured")

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/balance",
                    headers=self._get_headers(),
                    timeout=10.0,
                )
                response.raise_for_status()
                data = response.json()

        if not data.get("status"):
                    raise Exception(f"Paystack error: {data.get('message')}")

                result = data.get("data", [])
                logger.info(f"Account balance retrieved: {result}")

        return {
                    "balance": result[0].get("balance") if result else 0,
                    "currency": "NGN",
                }

        except Exception as e:
            logger.error(f"Failed to get balance: {str(e)}")
            raise

    def _get_headers(self) -> Dict[str, str]:

        """Get request headers for Paystack API.

        Returns:
            Dictionary with authorization headers
        """
        return {
            "Authorization": f"Bearer {self.secret_key}",
            "Content-Type": "application/json",
        }


# Global instance
        paystack_service = PaystackService()
