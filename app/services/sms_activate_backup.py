"""SMS-Activate backup service for when TextVerified is unavailable."""
import asyncio
from typing import Dict, Any, Optional
import httpx
from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)

class SMSActivateService:
    """SMS-Activate backup provider."""
    
    def __init__(self):
        self.api_key = getattr(settings, 'sms_activate_api_key', None)
        self.base_url = "https://sms-activate.org/stubs/handler_api.php"
        
    async def get_balance(self) -> Dict[str, Any]:
        """Get account balance."""
        if not self.api_key:
            return {"error": "SMS-Activate API key not configured"}
            
        try:
            params = {
                "api_key": self.api_key,
                "action": "getBalance"
            }
            
            async with httpx.AsyncClient(timeout=30) as client:
                response = await client.get(self.base_url, params=params)
                
                if response.status_code == 200:
                    balance_text = response.text.strip()
                    if balance_text.startswith("ACCESS_BALANCE:"):
                        balance = float(balance_text.split(":")[1])
                        return {"balance": balance, "currency": "RUB"}
                    else:
                        return {"error": balance_text}
                        
                return {"error": f"HTTP {response.status_code}"}
                
        except Exception as e:
            logger.error("SMS-Activate balance check failed: %s", e)
            return {"error": str(e)}
    
    async def get_services(self) -> Dict[str, Any]:
        """Get available services."""
        # SMS-Activate service mapping
        services = [
            {"id": "tg", "name": "telegram", "display_name": "Telegram", "price": 0.15},
            {"id": "wa", "name": "whatsapp", "display_name": "WhatsApp", "price": 0.20},
            {"id": "go", "name": "google", "display_name": "Google", "price": 0.10},
            {"id": "fb", "name": "facebook", "display_name": "Facebook", "price": 0.25},
            {"id": "ig", "name": "instagram", "display_name": "Instagram", "price": 0.30},
            {"id": "tw", "name": "twitter", "display_name": "Twitter", "price": 0.35},
        ]
        
        return {"services": services, "provider": "sms-activate"}
    
    async def create_verification(self, service_name: str, country: str = "0") -> Dict[str, Any]:
        """Create SMS verification."""
        if not self.api_key:
            return {"error": "SMS-Activate API key not configured"}
            
        # Map service names to SMS-Activate service codes
        service_map = {
            "telegram": "tg", "whatsapp": "wa", "google": "go",
            "facebook": "fb", "instagram": "ig", "twitter": "tw"
        }
        
        service_code = service_map.get(service_name.lower())
        if not service_code:
            return {"error": f"Service {service_name} not supported"}
            
        try:
            params = {
                "api_key": self.api_key,
                "action": "getNumber",
                "service": service_code,
                "country": country
            }
            
            async with httpx.AsyncClient(timeout=30) as client:
                response = await client.get(self.base_url, params=params)
                
                if response.status_code == 200:
                    result = response.text.strip()
                    
                    if result.startswith("ACCESS_NUMBER:"):
                        # Format: ACCESS_NUMBER:id:phone_number
                        parts = result.split(":")
                        if len(parts) >= 3:
                            return {
                                "phone_number": f"+{parts[2]}",
                                "number_id": parts[1],
                                "service": service_name,
                                "country": country,
                                "cost": 0.15,
                                "provider": "sms-activate"
                            }
                    
                    return {"error": result}
                    
                return {"error": f"HTTP {response.status_code}"}
                
        except Exception as e:
            logger.error("SMS-Activate number request failed: %s", e)
            return {"error": str(e)}
    
    async def get_sms(self, number_id: str) -> Dict[str, Any]:
        """Get SMS for verification."""
        if not self.api_key:
            return {"error": "SMS-Activate API key not configured"}
            
        try:
            params = {
                "api_key": self.api_key,
                "action": "getStatus",
                "id": number_id
            }
            
            async with httpx.AsyncClient(timeout=30) as client:
                response = await client.get(self.base_url, params=params)
                
                if response.status_code == 200:
                    result = response.text.strip()
                    
                    if result.startswith("STATUS_OK:"):
                        # Format: STATUS_OK:sms_code
                        sms_code = result.split(":", 1)[1]
                        return {"sms": sms_code, "provider": "sms-activate"}
                    elif result == "STATUS_WAIT_CODE":
                        return {"error": "No SMS received yet"}
                    else:
                        return {"error": result}
                        
                return {"error": f"HTTP {response.status_code}"}
                
        except Exception as e:
            logger.error("SMS-Activate SMS check failed: %s", e)
            return {"error": str(e)}

# Test function
async def test_sms_activate():
    """Test SMS-Activate integration."""
    service = SMSActivateService()
    
    print("Testing SMS-Activate...")
    
    # Test balance
    balance = await service.get_balance()
    print(f"Balance: {balance}")
    
    # Test services
    services = await service.get_services()
    print(f"Services: {len(services.get('services', []))} available")
    
    return balance.get("balance") is not None

if __name__ == "__main__":
    asyncio.run(test_sms_activate())