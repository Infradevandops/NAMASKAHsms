"""TextVerified API integration service."""

import os
import random
from typing import Any, Dict, List, Optional
from app.core.config import get_settings
from app.core.logging import get_logger

try:
    import textverified
except ImportError:
    textverified = None

logger = get_logger(__name__)


class TextVerifiedService:
    """Service for TextVerified API integration."""

    def __init__(self):
        """Initialize TextVerified service."""
        settings = get_settings()
        
        # Get credentials from environment
        self.api_key = os.getenv("TEXTVERIFIED_API_KEY")
        self.api_username = os.getenv("TEXTVERIFIED_USERNAME")
        
        # Check if TextVerified is available
        self.enabled = textverified is not None and self._validate_credentials()
        
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
            logger.warning("TextVerified service disabled - missing credentials or library")
            self.client = None

    def _validate_credentials(self) -> bool:
        """Validate that required credentials are present."""
        return bool(self.api_key and self.api_username)

    async def get_balance(self) -> Dict[str, Any]:
        """Get account balance from TextVerified."""
        if not self.enabled:
            return {"balance": 0.0, "error": "Service not available"}

        try:
            # This would be the actual API call
            # balance_data = await self.client.get_balance()
            # return balance_data
            
            # Mock response for now
            return {"balance": 100.0, "currency": "USD"}
            
        except Exception as e:
            logger.error(f"Failed to get TextVerified balance: {e}")
            return {"balance": 0.0, "error": str(e)}

    async def get_area_codes_list(self) -> List[Dict[str, Any]]:
        """Get list of available area codes."""
        if not self.enabled:
            # Return mock data if service is not available
            return self._get_mock_area_codes()

        try:
            # This would be the actual API call
            # area_codes = await self.client.get_area_codes()
            # return area_codes
            
            # Return mock data for now
            return self._get_mock_area_codes()
            
        except Exception as e:
            logger.error(f"Failed to get area codes: {e}")
            return self._get_mock_area_codes()

    def _get_mock_area_codes(self) -> List[Dict[str, Any]]:
        """Get mock US area codes for testing - TextVerified supports US only."""
        return [
            {"code": "212", "name": "New York, NY", "available": True},
            {"code": "213", "name": "Los Angeles, CA", "available": True},
            {"code": "312", "name": "Chicago, IL", "available": True},
            {"code": "415", "name": "San Francisco, CA", "available": True},
            {"code": "617", "name": "Boston, MA", "available": True},
            {"code": "713", "name": "Houston, TX", "available": True},
            {"code": "305", "name": "Miami, FL", "available": True},
            {"code": "206", "name": "Seattle, WA", "available": True},
            {"code": "404", "name": "Atlanta, GA", "available": True},
            {"code": "702", "name": "Las Vegas, NV", "available": True},
            {"code": "214", "name": "Dallas, TX", "available": True},
            {"code": "602", "name": "Phoenix, AZ", "available": True},
            {"code": "215", "name": "Philadelphia, PA", "available": True},
            {"code": "216", "name": "Cleveland, OH", "available": True},
            {"code": "303", "name": "Denver, CO", "available": True},
        ]

    async def get_services_list(self) -> List[Dict[str, Any]]:
        """Get list of available services."""
        if not self.enabled:
            return self._get_mock_services()

        try:
            # This would be the actual API call
            # services = await self.client.get_services()
            # return services
            
            # Return mock data for now
            return self._get_mock_services()
            
        except Exception as e:
            logger.error(f"Failed to get services: {e}")
            return self._get_mock_services()

    def _get_mock_services(self) -> List[Dict[str, Any]]:
        """Get mock services for testing - All services work with US numbers only."""
        return [
            {"id": "whatsapp", "name": "WhatsApp", "price": 2.50, "available": True, "country": "US"},
            {"id": "telegram", "name": "Telegram", "price": 2.00, "available": True, "country": "US"},
            {"id": "discord", "name": "Discord", "price": 2.25, "available": True, "country": "US"},
            {"id": "instagram", "name": "Instagram", "price": 2.75, "available": True, "country": "US"},
            {"id": "facebook", "name": "Facebook", "price": 2.50, "available": True, "country": "US"},
            {"id": "twitter", "name": "Twitter", "price": 2.50, "available": True, "country": "US"},
            {"id": "google", "name": "Google", "price": 2.00, "available": True, "country": "US"},
            {"id": "microsoft", "name": "Microsoft", "price": 2.25, "available": True, "country": "US"},
            {"id": "amazon", "name": "Amazon", "price": 2.50, "available": True, "country": "US"},
            {"id": "uber", "name": "Uber", "price": 2.75, "available": True, "country": "US"},
        ]

    async def purchase_number(
        self, 
        service: str, 
        area_code: Optional[str] = None,
        carrier: Optional[str] = None
    ) -> Dict[str, Any]:
        """Purchase a phone number for verification."""
        if not self.enabled:
            return {
                "success": False,
                "error": "TextVerified service not available",
                "verification_id": None
            }

        try:
            # This would be the actual API call
            # result = await self.client.purchase_number(
            #     service=service,
            #     area_code=area_code,
            #     carrier=carrier
            # )
            # return result
            
            # Mock response for now - US numbers only
            mock_id = f"tv_{random.randint(100000, 999999)}"
            # Generate US phone number with proper area code
            area_code = area_code or random.choice(["212", "213", "312", "415", "617", "713", "305", "206", "404", "702"])
            mock_number = f"+1{area_code}{random.randint(1000000, 9999999)}"
            
            return {
                "success": True,
                "verification_id": mock_id,
                "phone_number": mock_number,
                "service": service,
                "country": "US",
                "cost": 2.50,
                "expires_in": 600  # 10 minutes
            }
            
        except Exception as e:
            logger.error(f"Failed to purchase number: {e}")
            return {
                "success": False,
                "error": str(e),
                "verification_id": None
            }

    async def get_sms(self, verification_id: str) -> Dict[str, Any]:
        """Get SMS for a verification."""
        if not self.enabled:
            return {
                "success": False,
                "error": "TextVerified service not available",
                "sms": None
            }

        try:
            # This would be the actual API call
            # result = await self.client.get_sms(verification_id)
            # return result
            
            # Mock response for now
            mock_code = f"{random.randint(100000, 999999)}"
            
            return {
                "success": True,
                "sms": f"Your verification code is: {mock_code}",
                "code": mock_code,
                "received_at": "2024-01-01T12:00:00Z"
            }
            
        except Exception as e:
            logger.error(f"Failed to get SMS: {e}")
            return {
                "success": False,
                "error": str(e),
                "sms": None
            }

    async def cancel_verification(self, verification_id: str) -> Dict[str, Any]:
        """Cancel a verification."""
        if not self.enabled:
            return {"success": False, "error": "Service not available"}

        try:
            # This would be the actual API call
            # result = await self.client.cancel_verification(verification_id)
            # return result
            
            # Mock response for now
            return {"success": True, "message": "Verification cancelled"}
            
        except Exception as e:
            logger.error(f"Failed to cancel verification: {e}")
            return {"success": False, "error": str(e)}