"""TextVerified API Client using official SDK."""
import textverified
from textverified import NumberType, ReservationCapability
from typing import Dict, Any, Optional, List
from app.core.logging import get_logger
from app.core.config import get_settings

logger = get_logger(__name__)
settings = get_settings()


class TextVerifiedAPIClient:
    """Client for TextVerified API using official SDK."""

    def __init__(self):
        self.client = textverified.TextVerified(
            api_key=settings.textverified_api_key,
            api_username=getattr(settings, "textverified_email", "")
        )

    async def get_account_balance(self) -> Dict[str, Any]:
        """Get account balance from TextVerified API."""
        try:
            account = self.client.account.me()
            balance = float(account.current_balance)
            logger.info(f"TextVerified balance fetched: ${balance}")
            return {
                "balance": balance,
                "currency": "USD",
                "account_id": account.username,
            }
        except AttributeError as e:
            logger.error(f"TextVerified API attribute error (check API key): {e}")
            raise
        except Exception as e:
            logger.error(f"Failed to get account balance: {type(e).__name__}: {e}")
            raise

    async def create_verification(
        self,
        service: str,
        area_code: Optional[str] = None,
        carrier: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Create SMS verification and get phone number."""
        try:
            kwargs = {
                "service_name": service,
                "capability": ReservationCapability.SMS
            }
            if area_code:
                kwargs["area_code_select_option"] = [area_code]

            verification = self.client.verifications.create(**kwargs)

            return {
                "id": verification.id,
                "phone_number": verification.number,
                "cost": float(verification.total_cost),
                "status": verification.state,
            }
        except Exception as e:
            logger.error(f"Failed to create verification: {e}")
            raise Exception(f"Failed to create verification: {str(e)}")

    async def get_verification_status(self, verification_id: str) -> Dict[str, Any]:
        """Get verification status and details."""
        try:
            verification = self.client.verifications.details(verification_id)
            return {
                "id": verification.id,
                "status": verification.state,
                "phone_number": verification.number,
                "cost": float(verification.total_cost),
            }
        except Exception as e:
            logger.error(f"Failed to get verification status: {e}")
            raise Exception(f"Failed to get verification status: {str(e)}")

    async def get_sms_messages(self, reservation_id: str) -> List[Dict[str, Any]]:
        """Get SMS messages for a reservation."""
        try:
            messages = self.client.sms.list()
            result = []
            for msg in messages.data:
                if hasattr(msg, 'reservation_id') and msg.reservation_id == reservation_id:
                    result.append({
                        "id": msg.id,
                        "text": msg.sms_content,
                        "from": getattr(msg, "from", None),
                        "received_at": msg.created_at,
                    })
            return result
        except Exception as e:
            logger.error(f"Failed to get SMS messages: {e}")
            return []

    async def create_rental(
        self,
        service: str,
        duration_days: int,
        renewable: bool = False,
        area_code: Optional[str] = None,
        carrier: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Create phone number rental with optional area code and carrier selection."""
        try:
            duration_map = {7: "sevenDay", 30: "thirtyDay", 1: "oneDay"}
            duration = duration_map.get(duration_days, "sevenDay")

            kwargs = {
                "service_name": service,
                "capability": ReservationCapability.SMS,
                "duration": duration,
                "is_renewable": renewable
            }
            
            # Add area code if specified
            if area_code:
                kwargs["area_code_select_option"] = [area_code]
            
            # Add carrier if specified
            if carrier:
                kwargs["carrier_select_option"] = [carrier]

            rental = self.client.reservations.rental.create(**kwargs)

            return {
                "id": rental.id,
                "phone_number": rental.number,
                "cost": float(rental.total_cost),
                "expires_at": rental.created_at,
                "renewable": renewable,
                "area_code": area_code,
                "carrier": carrier,
            }
        except Exception as e:
            logger.error(f"Failed to create rental: {e}")
            raise Exception(f"Failed to create rental: {str(e)}")

    async def get_rentals(self, rental_type: str = "renewable") -> List[Dict[str, Any]]:
        """Get list of rentals (renewable or non-renewable)."""
        try:
            if rental_type == "renewable":
                rentals = self.client.reservations.rental.renewable.list()
            else:
                rentals = self.client.reservations.rental.nonrenewable.list()

            result = []
            for rental in rentals.data:
                result.append({
                    "id": rental.id,
                    "phone_number": rental.number,
                    "service": rental.service_name,
                    "expires_at": rental.created_at,
                    "status": rental.state,
                })
            return result
        except Exception as e:
            logger.error(f"Failed to get rentals: {e}")
            return []

    async def extend_rental(self, rental_id: str, duration_days: int) -> Dict[str, Any]:
        """Extend rental duration."""
        try:
            duration_map = {7: "sevenDay", 30: "thirtyDay", 1: "oneDay"}
            duration = duration_map.get(duration_days, "sevenDay")

            extension = self.client.reservations.rentals.extensions.create(
                rental_id=rental_id,
                extension_duration=duration
            )

            return {
                "id": extension.id,
                "expires_at": extension.created_at,
                "cost": float(extension.total_cost),
            }
        except Exception as e:
            logger.error(f"Failed to extend rental: {e}")
            raise Exception(f"Failed to extend rental: {str(e)}")

    async def get_services(self) -> List[Dict[str, Any]]:
        """Get available services from TextVerified."""
        try:
            from textverified import ReservationType
            services = self.client.services.list(
                number_type=NumberType.MOBILE,
                reservation_type=ReservationType.VERIFICATION
            )
            result = []
            seen_names = set()
            
            for service in services:
                # Extract service name from SDK object
                svc_name = getattr(service, 'service_name', None) or getattr(service, 'name', str(service))
                
                # Skip duplicates
                if svc_name in seen_names:
                    continue
                    
                seen_names.add(svc_name)
                result.append({
                    "id": svc_name.lower().replace(" ", ""),
                    "name": svc_name,
                    "category": "messaging"
                })
            return result
        except Exception as e:
            logger.error(f"Failed to get services from TextVerified: {e}")
            return []

    async def get_area_codes(self) -> List[Dict[str, Any]]:
        """Get available area codes."""
        try:
            codes = self.client.services.area_codes()
            result = []
            for code in codes:
                result.append({
                    "code": code.area_code,
                    "country": "US",
                    "region": code.state,
                })
            return result
        except Exception as e:
            logger.error(f"Failed to get area codes: {e}")
            return []

    async def get_pricing(
        self, service: str, reservation_type: str = "verification"
    ) -> Dict[str, Any]:
        """Get pricing for service."""
        try:
            if reservation_type == "verification":
                pricing = self.client.verifications.pricing(
                    service_name=service,
                    area_code=False,
                    carrier=False,
                    number_type=NumberType.MOBILE,
                    capability=ReservationCapability.SMS
                )
            else:
                pricing = self.client.reservations.rental.pricing(
                    service_name=service,
                    area_code=False,
                    number_type=NumberType.MOBILE,
                    capability=ReservationCapability.SMS,
                    is_renewable=True,
                    duration="sevenDay"
                )

            return {
                "service": service,
                "cost": float(pricing.price),
                "currency": "USD",
            }
        except Exception as e:
            logger.error(f"Failed to get pricing: {e}")
            return {"service": service, "cost": 0.0, "currency": "USD"}


# Global instance
_api_client: Optional[TextVerifiedAPIClient] = None


def get_textverified_client() -> TextVerifiedAPIClient:
    """Get or create TextVerified API client instance."""
    global _api_client
    if _api_client is None:
        _api_client = TextVerifiedAPIClient()
    return _api_client
