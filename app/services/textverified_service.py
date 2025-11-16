"""TextVerified provider service."""
import textverified
from typing import Dict, Optional, Any
from app.core.config import settings
from app.services.sms_provider_interface import SMSProviderInterface
from app.core.logging import get_logger

logger = get_logger(__name__)


class TextVerifiedService(SMSProviderInterface):
    """TextVerified provider implementation using official package."""

    def __init__(self):
        self.api_key = settings.textverified_api_key
        self.api_username = getattr(settings, 'textverified_email', 'huff_06psalm@icloud.com')
        self.enabled = bool(self.api_key and self.api_username)

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
            logger.warning("TextVerified API key or username not configured")
    
    async def get_balance(self) -> Dict[str, Any]:
        """Get account balance."""
        if not self.enabled:
            raise Exception("TextVerified not configured")
        try:
            balance = self.client.account.balance
            return {
                "balance": float(balance),
                "currency": "USD"
            }
        except Exception as e:
            raise Exception(f"TextVerified balance error: {str(e)}")
    
    async def buy_number(self, country: str, service: str) -> Dict[str, Any]:
        """Purchase phone number for verification."""
        if not self.enabled:
            raise Exception("TextVerified not configured")
        try:
            verification = self.client.verifications.create(
                service_name=service,
                capability=textverified.ReservationCapability.SMS
            )
            
            return {
                "activation_id": verification.id,
                "phone_number": f"+1{verification.number}",
                "cost": float(verification.total_cost)
            }
        except Exception as e:
            raise Exception(f"TextVerified purchase error: {str(e)}")
    
    async def check_sms(self, activation_id: str) -> Dict[str, Any]:
        """Check for SMS messages."""
        if not self.enabled:
            raise Exception("TextVerified not configured")
        try:
            verification = self.client.verifications.details(activation_id)
            
            # Check if SMS received
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
        except Exception as e:
            return {
                "sms_code": None,
                "sms_text": None,
                "status": "error",
                "error": str(e)
            }
    
    async def get_pricing(self, country: str, service: str) -> Dict[str, Any]:
        """Get service pricing."""
        # TextVerified has fixed pricing, typically $0.50-$2.00
        # This is a simplified implementation
        return {
            "cost": 0.50,
            "currency": "USD"
        }
    
    # Legacy methods for backward compatibility
    async def get_number(self, service: str, country: str = "US") -> Dict:
        """Get phone number for verification (legacy method)."""
        result = await self.buy_number(country, service)
        return {
            "id": result["activation_id"],
            "number": result["phone_number"],
            "cost": result["cost"]
        }
    
    async def get_sms(self, activation_id: str) -> Optional[str]:
        """Get SMS code for activation (legacy method)."""
        result = await self.check_sms(activation_id)
        return result.get("sms_code")
    
    async def cancel_activation(self, activation_id: str) -> bool:
        """Cancel activation and get refund."""
        if not self.enabled:
            return False
        try:
            self.client.verifications.cancel(activation_id)
            return True
        except Exception as e:
            logger.error(f"TextVerified cancel failed: {e}")
            return False
