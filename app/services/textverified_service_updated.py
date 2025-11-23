"""TextVerified provider service - Updated Error Handling"""
try:
    import textverified
except ImportError:
    textverified = None

from typing import Dict, Optional, Any

from app.core.config import settings
    TextVerifiedAPIError,
    ServiceUnavailableError,
    InvalidInputError,
)

logger = get_logger(__name__)


class TextVerifiedService(SMSProviderInterface):
    """TextVerified provider implementation using official package."""

    def __init__(self):
        self.api_key = settings.textverified_api_key
        self.api_username = getattr(settings,
                                    'textverified_email', 'huff_06psalm@icloud.com')
        self.enabled = bool(self.api_key and self.api_username and textverified)

        if self.enabled:
            try:
                self.client = textverified.TextVerified(
                    api_key=self.api_key,
                    api_username=self.api_username
                )
                logger.info("TextVerified client initialized successfully")
            except Exception as e:
                logger.error(f"TextVerified client initialization failed: {e}")
                self.enabled = False
        else:
            if not textverified:
                logger.warning("TextVerified package not installed")
            else:
                logger.warning("TextVerified API key or username not configured")

    async def get_balance(self) -> Dict[str, Any]:
        """Get account balance."""
        try:
            if not self.enabled:
                raise ServiceUnavailableError("TextVerified not configured")

            balance = self.client.account.balance
            return {
                "balance": float(balance),
                "currency": "USD"
            }
        except ServiceUnavailableError:
        pass
        except Exception as e:
            logger.error(f"TextVerified balance error: {str(e)}")
            raise TextVerifiedAPIError(f"Failed to get balance: {str(e)}")

    async def buy_number(self, country: str, service: str) -> Dict[str, Any]:
        """Purchase phone number for verification."""
        try:
            if not self.enabled:
                raise ServiceUnavailableError("TextVerified not configured")

            if not service:
                raise InvalidInputError("Service name is required")

            verification = self.client.verifications.create(
                service_name=service,
                capability=textverified.ReservationCapability.SMS
            )

            return {
                "activation_id": verification.id,
                "phone_number": f"+1{verification.number}",
                "cost": float(verification.total_cost)
            }
        except (ServiceUnavailableError, InvalidInputError):
            raise
        except Exception as e:
            logger.error(f"TextVerified purchase error: {str(e)}")
            raise TextVerifiedAPIError(f"Failed to purchase number: {str(e)}")

    async def check_sms(self, activation_id: str) -> Dict[str, Any]:
        """Check for SMS messages."""
        try:
            if not self.enabled:
                raise ServiceUnavailableError("TextVerified not configured")

            if not activation_id:
                raise InvalidInputError("Activation ID is required")

            verification = self.client.verifications.details(activation_id)

            if hasattr(verification, 'sms') and verification.sms:
                for sms in verification.sms:
                    if hasattr(sms, 'message'):
                        return {
                            "sms_code": sms.message,
                            "sms_text": sms.message,
                            "status": "received"
                        }

            return {
                "sms_code": None,
                "sms_text": None,
                "status": "pending"
            }
        except (ServiceUnavailableError, InvalidInputError):
            raise
        except Exception as e:
            logger.error(f"TextVerified check SMS error: {str(e)}")
            return {
                "sms_code": None,
                "sms_text": None,
                "status": "error",
                "error": str(e)
            }

    async def get_pricing(self, country: str, service: str) -> Dict[str, Any]:
        """Get service pricing."""
        try:
            if not service:
                raise InvalidInputError("Service name is required")

            return {
                "cost": 0.50,
                "currency": "USD"
            }
        except InvalidInputError:
        pass
        except Exception as e:
            logger.error(f"TextVerified pricing error: {str(e)}")
            raise TextVerifiedAPIError(f"Failed to get pricing: {str(e)}")

    async def get_number(self, service: str, country: str = "US") -> Dict:
        """Get phone number for verification (legacy method)."""
        try:
            result = await self.buy_number(country, service)
            return {
                "id": result["activation_id"],
                "number": result["phone_number"],
                "cost": result["cost"]
            }
        except (ServiceUnavailableError, InvalidInputError, TextVerifiedAPIError):
            raise
        except Exception as e:
            logger.error(f"TextVerified get_number error: {str(e)}")
            raise TextVerifiedAPIError(f"Failed to get number: {str(e)}")

    async def get_sms(self, activation_id: str) -> Optional[str]:
        """Get SMS code for activation (legacy method)."""
        try:
            result = await self.check_sms(activation_id)
            return result.get("sms_code")
        except (ServiceUnavailableError, InvalidInputError):
            raise
        except Exception as e:
            logger.error(f"TextVerified get_sms error: {str(e)}")
            raise TextVerifiedAPIError(f"Failed to get SMS: {str(e)}")

    async def cancel_activation(self, activation_id: str) -> bool:
        """Cancel activation and get refund."""
        try:
            if not self.enabled:
                raise ServiceUnavailableError("TextVerified not configured")

            if not activation_id:
                raise InvalidInputError("Activation ID is required")

            self.client.verifications.cancel(activation_id)
            return True
        except (ServiceUnavailableError, InvalidInputError):
            raise
        except Exception as e:
            logger.error(f"TextVerified cancel failed: {str(e)}")
            raise TextVerifiedAPIError(f"Failed to cancel activation: {str(e)}")
