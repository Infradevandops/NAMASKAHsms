"""TextVerified provider service."""
import httpx
from typing import Dict, Optional
from app.core.config import settings
from app.services.sms_provider_interface import SMSProviderInterface

class TextVerifiedService(SMSProviderInterface):
    """TextVerified provider implementation."""
    
    def __init__(self):
        self.base_url = "https://www.textverified.com/api"
        self.api_key = settings.textverified_api_key
    
    async def get_balance(self) -> float:
        """Get account balance."""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/Users/{self.api_key}/balance"
            )
            data = response.json()
            return float(data.get("credit_balance", 0))
    
    async def get_number(self, service: str, country: str = "US") -> Dict:
        """Get phone number for verification."""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/Users/{self.api_key}/requests",
                json={
                    "service": service,
                    "country": country
                }
            )
            
            data = response.json()
            if data.get("success"):
                return {
                    "id": data["id"],
                    "number": data["number"],
                    "cost": data.get("price", 0.5)
                }
            raise Exception(f"Failed to get number: {data.get('message')}")
    
    async def get_sms(self, activation_id: str) -> Optional[str]:
        """Get SMS code for activation."""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/Users/{self.api_key}/requests/{activation_id}"
            )
            
            data = response.json()
            if data.get("success") and data.get("sms"):
                return data["sms"]
            return None
    
    async def cancel_activation(self, activation_id: str) -> bool:
        """Cancel activation and get refund."""
        async with httpx.AsyncClient() as client:
            response = await client.delete(
                f"{self.base_url}/Users/{self.api_key}/requests/{activation_id}"
            )
            return response.status_code == 200