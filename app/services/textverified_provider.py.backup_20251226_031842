"""TextVerified provider implementation with unified interface."""
try:
    import textverified
except ImportError:
    textverified = None

from typing import Dict, Any
from app.core.config import settings

logger = get_logger(__name__)


class TextVerifiedProvider(SMSProvider):
    """TextVerified provider with unified interface."""

    def __init__(self):
        super().__init__("textverified", max_retries=3, timeout=30)

        self.api_key = settings.textverified_api_key
        self.api_username = getattr(settings,
                                    'textverified_email', 'huff_06psalm@icloud.com')
        self.client = None

        if self.api_key and self.api_username and textverified:
            try:
                self.client = textverified.TextVerified(
                    api_key=self.api_key,
                    api_username=self.api_username
                )
                self.enabled = True
                logger.info("TextVerified provider initialized")
            except Exception as e:
                logger.error(f"TextVerified initialization failed: {e}")
                self.enabled = False
        else:
            if not textverified:
                logger.warning("TextVerified package not installed")
            else:
                logger.warning("TextVerified credentials not configured")

    async def _get_balance(self) -> Dict[str, Any]:
        """Get account balance."""
        if not self.enabled or not self.client:
            raise Exception("TextVerified not configured")

        try:
            balance = self.client.account.balance
            return {
                "balance": float(balance),
                "currency": "USD",
                "provider": "textverified"
            }
        except Exception as e:
            raise Exception(f"TextVerified balance error: {str(e)}")

    async def _buy_number(self, country: str, service: str) -> Dict[str, Any]:
        """Purchase phone number."""
        if not self.enabled or not self.client:
            raise Exception("TextVerified not configured")

        try:
            verification = self.client.verifications.create(
                service_name=service,
                capability=textverified.ReservationCapability.SMS
            )

            return {
                "activation_id": verification.id,
                "phone_number": f"+1{verification.number}",
                "cost": float(verification.total_cost),
                "provider": "textverified",
                "country": country,
                "service": service
            }
        except Exception as e:
            raise Exception(f"TextVerified purchase error: {str(e)}")

    async def _check_sms(self, activation_id: str) -> Dict[str, Any]:
        """Check for SMS messages."""
        if not self.enabled or not self.client:
            raise Exception("TextVerified not configured")

        try:
            verification = self.client.verifications.details(activation_id)

            if hasattr(verification, 'sms') and verification.sms:
                for sms in verification.sms:
                    if hasattr(sms, 'message'):
                        return {
                            "sms_code": sms.message,
                            "sms_text": sms.message,
                            "status": "received",
                            "provider": "textverified"
                        }

            return {
                "sms_code": None,
                "sms_text": None,
                "status": "pending",
                "provider": "textverified"
            }
        except Exception as e:
            return {
                "sms_code": None,
                "sms_text": None,
                "status": "error",
                "error": str(e),
                "provider": "textverified"
            }

    async def _get_pricing(self, country: str, service: str) -> Dict[str, Any]:
        """Get service pricing."""
        return {
            "cost": 0.50,
            "currency": "USD",
            "provider": "textverified",
            "country": country,
            "service": service
        }

    async def cancel_activation(self, activation_id: str) -> bool:
        """Cancel activation and get refund."""
        if not self.enabled or not self.client:
            return False

        try:
            self.client.verifications.cancel(activation_id)
            return True
        except Exception as e:
            logger.error(f"TextVerified cancel failed: {e}")
            return False
