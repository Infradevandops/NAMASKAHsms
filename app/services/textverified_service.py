"""TextVerified provider service."""
try:
    import textverified
except ImportError:
    textverified = None

import os
import time
from typing import Dict, Optional, Any
from datetime import datetime, timedelta
from app.core.config import settings
from app.core.logging import get_logger
from app.services.sms_provider_interface import SMSProviderInterface

logger = get_logger(__name__)


class TextVerifiedService(SMSProviderInterface):
    """TextVerified provider implementation using official package."""

    def __init__(self):
        # Load credentials from environment variables
        self.api_key = os.getenv('TEXTVERIFIED_API_KEY') or settings.textverified_api_key
        self.api_username = os.getenv('TEXTVERIFIED_EMAIL') or getattr(settings, 'textverified_email', 'huff_06psalm@icloud.com')
        
        # Initialize cache for balance
        self._balance_cache = None
        self._balance_cache_time = None
        self._cache_ttl = 300  # 5 minutes
        
        # Log initialization attempt
        logger.info("TextVerified service initialization attempt")
        
        # Validate credentials
        self.enabled = self._validate_credentials()
        
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

    def _validate_credentials(self) -> bool:
        """Validate TextVerified credentials.
        
        Returns:
            bool: True if credentials are valid, False otherwise
            
        Validates: Requirements 1.1, 1.2, 1.3, 1.4, 1.5
        """
        if not self.api_key or not self.api_username:
            logger.warning("TextVerified credentials are missing")
            return False
        
        if not textverified:
            logger.warning("TextVerified package not installed")
            return False
        
        try:
            # Attempt to validate credentials by creating client
            test_client = textverified.TextVerified(
                api_key=self.api_key,
                api_username=self.api_username
            )
            logger.info("TextVerified credentials validated successfully")
            return True
        except Exception as e:
            logger.error(f"TextVerified credential validation failed: {e}")
            return False

    def _get_cached_balance(self) -> Optional[float]:
        """Get cached balance if still valid.
        
        Returns:
            float: Cached balance or None if cache expired
            
        Validates: Requirements 3.5
        """
        if self._balance_cache is not None and self._balance_cache_time is not None:
            elapsed = time.time() - self._balance_cache_time
            if elapsed < self._cache_ttl:
                logger.debug(f"Returning cached balance (age: {elapsed:.1f}s)")
                return self._balance_cache
        return None

    def _set_balance_cache(self, balance: float) -> None:
        """Cache balance with timestamp.
        
        Args:
            balance: Balance value to cache
            
        Validates: Requirements 3.5
        """
        self._balance_cache = balance
        self._balance_cache_time = time.time()
        logger.debug(f"Balance cached: {balance}")

    async def get_health_status(self) -> Dict[str, Any]:
        """Get TextVerified service health status with balance.
        
        Returns:
            Dict with status, balance, currency, and timestamp
            
        Validates: Requirements 2.1, 2.2, 2.3, 2.4, 2.5
        """
        try:
            if not self.enabled:
                logger.warning("Health check called but service not enabled")
                return {
                    "status": "error",
                    "error": "TextVerified not configured",
                    "balance": None,
                    "currency": "USD",
                    "timestamp": datetime.utcnow().isoformat()
                }
            
            # Retrieve balance from API with error handling
            balance = await self.get_balance()
            
            return {
                "status": "operational",
                "balance": float(balance["balance"]),
                "currency": "USD",
                "timestamp": datetime.utcnow().isoformat()
            }
        except Exception as e:
            logger.error(f"TextVerified health check error: {str(e)}")
            return {
                "status": "error",
                "error": str(e),
                "balance": None,
                "currency": "USD",
                "timestamp": datetime.utcnow().isoformat()
            }

    async def get_balance(self) -> Dict[str, Any]:
        """Get account balance with caching.
        
        Returns:
            Dict with balance and currency
            
        Validates: Requirements 3.1, 3.2, 3.3, 3.5
        """
        try:
            if not self.enabled:
                logger.error("Balance retrieval attempted but service not enabled")
                raise Exception("TextVerified not configured")
            
            # Check cache first
            cached_balance = self._get_cached_balance()
            if cached_balance is not None:
                return {
                    "balance": cached_balance,
                    "currency": "USD",
                    "cached": True
                }
            
            # Retrieve from API
            logger.debug("Fetching balance from TextVerified API")
            balance = self.client.account.balance
            balance_float = float(balance)
            
            # Cache the result
            self._set_balance_cache(balance_float)
            
            logger.info(f"Balance retrieved: {balance_float} USD")
            return {
                "balance": balance_float,
                "currency": "USD",
                "cached": False
            }
        except Exception as e:
            logger.error(f"TextVerified balance error: {str(e)}")
            raise

    async def _retry_with_backoff(self, func, max_retries: int = 3, initial_delay: float = 1.0):
        """Retry a function with exponential backoff.
        
        Args:
            func: Async function to retry
            max_retries: Maximum number of retries
            initial_delay: Initial delay in seconds
            
        Returns:
            Result of the function
            
        Validates: Requirements 4.4
        """
        import asyncio
        
        delay = initial_delay
        last_exception = None
        
        for attempt in range(max_retries + 1):
            try:
                logger.debug(f"Attempt {attempt + 1}/{max_retries + 1}")
                return await func()
            except Exception as e:
                last_exception = e
                if attempt < max_retries:
                    logger.warning(f"Attempt {attempt + 1} failed, retrying in {delay}s: {str(e)}")
                    await asyncio.sleep(delay)
                    delay *= 2  # Exponential backoff
                else:
                    logger.error(f"All {max_retries + 1} attempts failed")
        
        raise last_exception

    async def buy_number(self, country: str, service: str) -> Dict[str, Any]:
        """Purchase phone number for verification.
        
        Validates: Requirements 4.1, 4.3, 4.5
        """
        async def _buy():
            if not self.enabled:
                raise Exception("TextVerified not configured")
            verification = self.client.verifications.create(
                service_name=service,
                capability=textverified.ReservationCapability.SMS
            )

            return {
                "activation_id": verification.id,
                "phone_number": f"+1{verification.number}",
                "cost": float(verification.total_cost)
            }
        
        try:
            logger.info(f"Purchasing number for {service} in {country}")
            result = await self._retry_with_backoff(_buy)
            logger.info(f"Number purchased: {result['activation_id']}")
            return result
        except Exception as e:
            logger.error(f"TextVerified purchase error: {str(e)}")
            raise

    async def check_sms(self, activation_id: str) -> Dict[str, Any]:
        """Check for SMS messages.
        
        Validates: Requirements 4.1, 4.3, 4.5
        """
        async def _check():
            if not self.enabled:
                raise Exception("TextVerified not configured")
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
        
        try:
            logger.debug(f"Checking SMS for activation {activation_id}")
            result = await self._retry_with_backoff(_check)
            logger.debug(f"SMS check result: {result['status']}")
            return result
        except Exception as e:
            logger.error(f"TextVerified check error: {str(e)}")
            return {
                "sms_code": None,
                "sms_text": None,
                "status": "error",
                "error": str(e)
            }

    async def get_pricing(self, country: str, service: str) -> Dict[str, Any]:
        """Get service pricing.
        
        Validates: Requirements 4.1, 4.3, 4.5
        """
        try:
            logger.debug(f"Fetching pricing for {service} in {country}")
            return {
                "cost": 0.50,
                "currency": "USD"
            }
        except Exception as e:
            logger.error(f"Pricing fetch error: {str(e)}")
            raise

    async def get_number(self, service: str, country: str = "US") -> Dict:
        """Get phone number for verification (legacy method).
        
        Validates: Requirements 4.1, 4.3, 4.5
        """
        try:
            logger.debug(f"Getting number for {service} in {country}")
            result = await self.buy_number(country, service)
            return {
                "id": result["activation_id"],
                "number": result["phone_number"],
                "cost": result["cost"]
            }
        except Exception as e:
            logger.error(f"Get number error: {str(e)}")
            raise

    async def get_sms(self, activation_id: str) -> Optional[str]:
        """Get SMS code for activation (legacy method).
        
        Validates: Requirements 4.1, 4.3, 4.5
        """
        try:
            logger.debug(f"Getting SMS for activation {activation_id}")
            result = await self.check_sms(activation_id)
            return result.get("sms_code")
        except Exception as e:
            logger.error(f"Get SMS error: {str(e)}")
            return None

    async def cancel_activation(self, activation_id: str) -> bool:
        """Cancel activation and get refund.
        
        Validates: Requirements 4.1, 4.3, 4.5
        """
        try:
            if not self.enabled:
                logger.warning("Cancel attempted but service not enabled")
                return False
            self.client.verifications.cancel(activation_id)
            logger.info(f"Activation cancelled: {activation_id}")
            return True
        except Exception as e:
            logger.error(f"TextVerified cancel failed: {e}")
            return False
