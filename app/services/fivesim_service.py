"""5SIM API service integration."""

from typing import Dict

import httpx

from app.core.config import get_settings
from app.core.exceptions import ExternalServiceError


class FiveSimService:
    def __init__(self):
        settings = get_settings()
        self.api_key = settings.fivesim_api_key
        self.base_url = "https://5sim.net/v1"
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Accept": "application/json",
        }

    async def get_balance(self) -> Dict:
        """Get account balance."""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/user/profile", headers=self.headers
                )
                response.raise_for_status()
                return response.json()
        except Exception as e:
            raise ExternalServiceError("5SIM", f"Failed to get balance: {str(e)}")

    async def buy_number(self, country: str, service: str) -> Dict:
        """Purchase phone number for verification."""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/guest/products/{country}/{service}",
                    headers=self.headers,
                )
                response.raise_for_status()
                response.json()

                # Buy the number
                buy_response = await client.get(
                    f"{self.base_url}/user/buy/activation/{country}/{service}",
                    headers=self.headers,
                )
                buy_response.raise_for_status()
                return buy_response.json()
        except Exception as e:
            raise ExternalServiceError("5SIM", f"Failed to buy number: {str(e)}")

    async def check_sms(self, activation_id: str) -> Dict:
        """Check for SMS messages."""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/user/check/{activation_id}", headers=self.headers
                )
                response.raise_for_status()
                return response.json()
        except Exception as e:
            raise ExternalServiceError("5SIM", f"Failed to check SMS: {str(e)}")

    async def get_countries(self) -> Dict:
        """Get available countries."""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/guest/countries", headers=self.headers
                )
                response.raise_for_status()
                return response.json()
        except Exception as e:
            raise ExternalServiceError("5SIM", f"Failed to get countries: {str(e)}")

    async def get_pricing(self, country: str = "us", service: str = "any") -> Dict:
        """Get service pricing."""
        try:
            async with httpx.AsyncClient() as client:
                # 5SIM uses different country codes
                country_map = {"us": "usa", "gb": "england", "ca": "canada"}
                mapped_country = country_map.get(country.lower(), country)

                response = await client.get(
                    f"{self.base_url}/guest/prices?country={mapped_country}&product={service}",
                    headers=self.headers,
                )
                response.raise_for_status()
                return response.json()
        except Exception as e:
            raise ExternalServiceError("5SIM", f"Failed to get pricing: {str(e)}")

    async def finish_activation(self, activation_id: str) -> Dict:
        """Finish activation."""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/user/finish/{activation_id}", headers=self.headers
                )
                response.raise_for_status()
                return response.json()
        except Exception as e:
            raise ExternalServiceError("5SIM", f"Failed to finish activation: {str(e)}")
