"""SMS-Activate API integration - Working SMS verification service."""
import asyncio
import httpx
from typing import Dict, Any, Optional
from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)

class SMSActivateService:
    """Production SMS verification using SMS-Activate API."""
    
    def __init__(self):
        # SMS-Activate is a reliable alternative to TextVerified
        self.api_key = settings.textverified_api_key  # Reuse the same env var
        self.base_url = "https://api.sms-activate.org/stubs/handler_api.php"
        self.timeout = 30
        
    async def _make_request(self, action: str, **params) -> str:
        """Make request to SMS-Activate API."""
        request_params = {
            "api_key": self.api_key,
            "action": action,
            **params
        }
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(self.base_url, params=request_params)
                
                if response.status_code == 200:
                    result = response.text.strip()
                    logger.info("SMS-Activate API %s: %s", action, result)
                    return result
                else:
                    logger.error("SMS-Activate API error: %s", response.status_code)
                    return "ERROR:{}".format(response.status_code)
                    
        except Exception as e:
            logger.error("SMS-Activate request failed: %s", e)
            return "ERROR:{}".format(str(e))
    
    async def get_balance(self) -> Dict[str, Any]:
        """Get account balance."""
        result = await self._make_request("getBalance")
        
        if result.startswith("ACCESS_BALANCE:"):
            balance = result.replace("ACCESS_BALANCE:", "")
            return {"balance": float(balance), "currency": "RUB"}
        else:
            return {"error": result}
    
    async def get_services(self) -> Dict[str, Any]:
        """Get available services."""
        # SMS-Activate service IDs (most popular)
        services = [
            {"id": "tg", "name": "Telegram", "price": 15},
            {"id": "wa", "name": "WhatsApp", "price": 20},
            {"id": "go", "name": "Google", "price": 10},
            {"id": "fb", "name": "Facebook", "price": 25},
            {"id": "ig", "name": "Instagram", "price": 30},
            {"id": "tw", "name": "Twitter", "price": 35},
            {"id": "dc", "name": "Discord", "price": 15},
            {"id": "ms", "name": "Microsoft", "price": 20},
            {"id": "am", "name": "Amazon", "price": 25},
            {"id": "pp", "name": "PayPal", "price": 40}
        ]
        
        return {"services": services}
    
    async def get_number(self, service: str, country: int = 0) -> Dict[str, Any]:
        """Get phone number for verification."""
        result = await self._make_request("getNumber", service=service, country=country)
        
        if result.startswith("ACCESS_NUMBER:"):
            parts = result.replace("ACCESS_NUMBER:", "").split(":")
            if len(parts) == 2:
                activation_id, phone_number = parts
                return {
                    "id": activation_id,
                    "number": phone_number,
                    "service": service,
                    "country": country
                }
        
        return {"error": result}
    
    async def get_sms(self, activation_id: str) -> Dict[str, Any]:
        """Get SMS code for activation."""
        result = await self._make_request("getStatus", id=activation_id)
        
        if result.startswith("STATUS_OK:"):
            code = result.replace("STATUS_OK:", "")
            return {"sms": code, "status": "completed"}
        elif result == "STATUS_WAIT_CODE":
            return {"status": "waiting"}
        elif result == "STATUS_WAIT_RETRY":
            return {"status": "retry"}
        else:
            return {"error": result}
    
    async def cancel_number(self, activation_id: str) -> Dict[str, Any]:
        """Cancel activation."""
        result = await self._make_request("setStatus", status="8", id=activation_id)
        
        if result == "ACCESS_CANCEL":
            return {"success": True}
        else:
            return {"error": result}
    
    async def create_verification(self, service_name: str, country: str = "US") -> Dict[str, Any]:
        """Create SMS verification."""
        # Map service names to SMS-Activate service codes
        service_mapping = {
            "telegram": "tg", "whatsapp": "wa", "google": "go",
            "facebook": "fb", "instagram": "ig", "twitter": "tw",
            "discord": "dc", "microsoft": "ms", "amazon": "am",
            "paypal": "pp", "netflix": "nf", "spotify": "sp"
        }
        
        # Map country codes to SMS-Activate country IDs
        country_mapping = {
            "US": 0, "RU": 0, "UA": 1, "KZ": 2, "CN": 3,
            "PH": 4, "MM": 5, "ID": 6, "MY": 7, "KE": 8,
            "TZ": 9, "VN": 10, "KG": 11, "IL": 13,
            "HK": 14, "PL": 15, "GB": 16, "MG": 17, "ZA": 18,
            "EG": 19, "IN": 22, "IE": 23, "KH": 24, "LA": 25,
            "HT": 26, "CI": 27, "GM": 28, "RS": 29, "YE": 30
        }
        
        service_code = service_mapping.get(service_name.lower(), "tg")
        country_id = country_mapping.get(country, 0)
        
        # Get phone number
        number_result = await self.get_number(service_code, country_id)
        
        if "error" in number_result:
            return number_result
        
        return {
            "phone_number": number_result["number"],
            "number_id": number_result["id"],
            "service": service_name,
            "country": country,
            "cost": 0.50  # Approximate cost in USD
        }
    
    async def poll_for_code(self, activation_id: str, max_attempts: int = 30) -> Dict[str, Any]:
        """Poll for SMS code."""
        for attempt in range(max_attempts):
            result = await self.get_sms(activation_id)
            
            if "sms" in result:
                return {"success": True, "code": result["sms"], "attempts": attempt + 1}
            elif result.get("status") == "waiting":
                await asyncio.sleep(5)  # Wait 5 seconds between checks
            else:
                return {"success": False, "error": result.get("error", "Unknown error")}
        
        return {"success": False, "error": "Timeout waiting for SMS", "attempts": max_attempts}

# Create service instance
sms_activate_service = SMSActivateService()