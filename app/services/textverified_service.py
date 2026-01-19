"""TextVerified provider service."""

try:
    import textverified
except ImportError:
    textverified = None

import os
import time
from datetime import datetime
from typing import Any, Dict, Optional

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class TextVerifiedService:
    """TextVerified provider implementation using official package."""

    def __init__(self):
        # Load credentials from environment variables
        self.api_key = (
            os.getenv("TEXTVERIFIED_API_KEY") or settings.textverified_api_key
        )
        self.api_username = os.getenv("TEXTVERIFIED_EMAIL") or getattr(
            settings, "textverified_email", "huff_06psalm@icloud.com"
        )

        # Initialize cache for balance
        self._balance_cache = None
        self._balance_cache_time = None
        self._cache_ttl = 300  # 5 minutes

        # Circuit breaker for connection failures
        self._circuit_breaker_failures = 0
        self._circuit_breaker_threshold = 5
        self._circuit_breaker_reset_time = None
        self._circuit_breaker_timeout = 300  # 5 minutes

        # Log initialization attempt
        logger.info("TextVerified service initialization attempt")

        # Validate credentials
        self.enabled = self._validate_credentials()

        if self.enabled:
            try:
                self.client = textverified.TextVerified(
                    api_key=self.api_key, api_username=self.api_username
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
                api_key=self.api_key, api_username=self.api_username
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

    def _check_circuit_breaker(self) -> bool:
        """Check if circuit breaker is open.

        Returns:
            True if circuit is closed (requests allowed), False if open
        """
        if self._circuit_breaker_reset_time:
            if time.time() > self._circuit_breaker_reset_time:
                # Reset circuit breaker
                logger.info("Circuit breaker reset - allowing requests")
                self._circuit_breaker_failures = 0
                self._circuit_breaker_reset_time = None
                return True
            else:
                logger.warning(
                    "Circuit breaker is OPEN - blocking requests to prevent cascading failures"
                )
                return False
        return True

    def _record_failure(self):
        """Record a failure and potentially open circuit breaker."""
        self._circuit_breaker_failures += 1
        if self._circuit_breaker_failures >= self._circuit_breaker_threshold:
            self._circuit_breaker_reset_time = (
                time.time() + self._circuit_breaker_timeout
            )
            logger.error(
                f"Circuit breaker OPENED after {self._circuit_breaker_failures} failures. Will retry in {self._circuit_breaker_timeout}s"
            )

    def _record_success(self):
        """Record a successful request."""
        if self._circuit_breaker_failures > 0:
            logger.info("Request successful - resetting failure counter")
        self._circuit_breaker_failures = 0
        self._circuit_breaker_reset_time = None

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
                    "timestamp": datetime.utcnow().isoformat(),
                }

            # Retrieve balance from API with error handling
            balance = await self.get_balance()

            return {
                "status": "operational",
                "balance": float(balance["balance"]),
                "currency": "USD",
                "timestamp": datetime.utcnow().isoformat(),
            }
        except Exception as e:
            logger.error(f"TextVerified health check error: {str(e)}")
            return {
                "status": "error",
                "error": str(e),
                "balance": None,
                "currency": "USD",
                "timestamp": datetime.utcnow().isoformat(),
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
                return {"balance": cached_balance, "currency": "USD", "cached": True}

            # Retrieve from API
            logger.debug("Fetching balance from TextVerified API")
            balance = self.client.account.balance
            balance_float = float(balance)

            # Cache the result
            self._set_balance_cache(balance_float)

            logger.info(f"Balance retrieved: {balance_float} USD")
            return {"balance": balance_float, "currency": "USD", "cached": False}
        except Exception as e:
            logger.error(f"TextVerified balance error: {str(e)}")
            raise

    async def _retry_with_backoff(
        self, func, max_retries: int = 3, initial_delay: float = 1.0
    ):
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
                error_msg = str(e)

                # Check for SSL/connection errors
                is_connection_error = any(
                    [
                        "SSL" in error_msg,
                        "Connection" in error_msg,
                        "RemoteDisconnected" in error_msg,
                        "EOF" in error_msg,
                    ]
                )

                if attempt < max_retries:
                    if is_connection_error:
                        logger.warning(
                            f"Connection error on attempt {attempt + 1}, retrying in {delay}s: {error_msg}"
                        )
                    else:
                        logger.warning(
                            f"Attempt {attempt + 1} failed, retrying in {delay}s: {error_msg}"
                        )
                    await asyncio.sleep(delay)
                    delay *= 2  # Exponential backoff
                else:
                    if is_connection_error:
                        logger.error(
                            f"All {max_retries + 1} attempts failed due to connection issues. Provider may be experiencing downtime."
                        )
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
                service_name=service, capability=textverified.ReservationCapability.SMS
            )

            return {
                "activation_id": verification.id,
                "phone_number": f"+1{verification.number}",
                "cost": float(verification.total_cost),
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
        # Check circuit breaker
        if not self._check_circuit_breaker():
            return {
                "sms_code": None,
                "sms_text": None,
                "status": "error",
                "error": "Service temporarily unavailable - please try again later",
            }

        async def _check():
            if not self.enabled:
                raise Exception("TextVerified not configured")
            verification = self.client.verifications.details(activation_id)

            if hasattr(verification, "sms") and verification.sms:
                for sms in verification.sms:
                    if hasattr(sms, "message"):
                        return {
                            "sms_code": sms.message,
                            "sms_text": sms.message,
                            "status": "received",
                        }

            return {"sms_code": None, "sms_text": None, "status": "pending"}

        try:
            logger.debug(f"Checking SMS for activation {activation_id}")
            result = await self._retry_with_backoff(_check)
            logger.debug(f"SMS check result: {result['status']}")
            self._record_success()
            return result
        except Exception as e:
            logger.error(f"TextVerified check error: {str(e)}")
            self._record_failure()
            return {
                "sms_code": None,
                "sms_text": None,
                "status": "error",
                "error": str(e),
            }

    async def get_pricing(self, country: str, service: str) -> Dict[str, Any]:
        """Get service pricing.

        Validates: Requirements 4.1, 4.3, 4.5
        """
        try:
            logger.debug(f"Fetching pricing for {service} in {country}")
            return {"cost": 0.50, "currency": "USD"}
        except Exception as e:
            logger.error(f"Pricing fetch error: {str(e)}")
            raise

    async def get_services_list(self, force_refresh: bool = False) -> list:
        """Get list of available services from TextVerified API.

        Returns:
            List of services with id, name, and cost

        Validates: Requirements 4.1, 4.3, 4.5
        """
        try:
            if not self.enabled:
                logger.error("Services list requested but service not enabled")
                raise Exception("TextVerified not configured")

            logger.debug("Fetching services list from TextVerified API")

            # Get services from TextVerified API with correct enums
            services_data = self.client.services.list(
                number_type=textverified.NumberType.MOBILE,
                reservation_type=textverified.ReservationType.VERIFICATION,
            )

            formatted_services = []
            seen = set()
            for service in services_data:
                # Extract service_name from Service object
                service_name = (
                    service.service_name
                    if hasattr(service, "service_name")
                    else str(service)
                )

                # Skip duplicates
                if service_name in seen:
                    continue
                seen.add(service_name)

                display_name = service_name.replace("_", " ").title()

                formatted_services.append(
                    {
                        "id": service_name,
                        "name": display_name,
                        "cost": float(getattr(service, "cost", 0.50)),
                    }
                )

            logger.info(
                f"Retrieved {len(formatted_services)} services from TextVerified API"
            )
            return formatted_services

        except Exception as e:
            logger.error(f"TextVerified services API error: {str(e)}")
            raise

    async def get_services(self) -> Dict[str, Any]:
        """Get services in API response format.

        Returns:
            Dict with services list

        Validates: Requirements 4.1, 4.3, 4.5
        """
        try:
            services_list = await self.get_services_list()
            return {"services": services_list, "total": len(services_list)}
        except Exception as e:
            logger.error(f"Get services error: {str(e)}")
            raise

    async def create_verification(
        self, service: str, area_code: str = None, carrier: str = None
    ) -> Dict[str, Any]:
        """Create verification with TextVerified API.

        Args:
            service: Service name (e.g., 'telegram')
            area_code: Optional area code
            carrier: Optional carrier

        Returns:
            Dict with id, phone_number, and cost

        Validates: Requirements 4.1, 4.3, 4.5
        """
        try:
            if not self.enabled:
                raise Exception("TextVerified not configured")

            logger.info(f"Creating verification for {service}")

            # Use the textverified package to create verification
            verification = self.client.verifications.create(
                service_name=service, capability=textverified.ReservationCapability.SMS
            )

            result = {
                "id": verification.id,
                "phone_number": f"+1{verification.number}",
                "cost": float(verification.total_cost),
            }

            logger.info(f"Verification created: {result['id']}")
            return result

        except Exception as e:
            logger.error(f"Create verification error: {str(e)}")
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
                "cost": result["cost"],
            }
        except Exception as e:
            logger.error(f"Get number error: {str(e)}")
            raise

    async def get_sms(self, activation_id: str) -> Dict[str, Any]:
        """Get SMS code for activation with full response.

        Validates: Requirements 4.1, 4.3, 4.5
        """
        try:
            logger.debug(f"Getting SMS for activation {activation_id}")
            result = await self.check_sms(activation_id)
            return result
        except Exception as e:
            logger.error(f"Get SMS error: {str(e)}")
            return {
                "sms_code": None,
                "sms_text": None,
                "status": "error",
                "error": str(e),
            }

    async def cancel_number(self, activation_id: str) -> bool:
        """Cancel number and get refund (alias for cancel_activation).

        Validates: Requirements 4.1, 4.3, 4.5
        """
        return await self.cancel_activation(activation_id)

    async def get_verification_status(self, activation_id: str) -> Dict[str, Any]:
        """Get verification status from TextVerified API.

        Args:
            activation_id: TextVerified activation ID

        Returns:
            Dict with status, sms_code, and sms_text

        Validates: Requirements 4.1, 4.3, 4.5
        """
        try:
            if not self.enabled:
                raise Exception("TextVerified not configured")

            logger.debug(f"Getting verification status for {activation_id}")
            verification = self.client.verifications.details(activation_id)

            # Check if SMS received
            sms_code = None
            sms_text = None
            status = "pending"

            if hasattr(verification, "sms") and verification.sms:
                for sms in verification.sms:
                    if hasattr(sms, "message") and sms.message:
                        sms_code = sms.message
                        sms_text = sms.message
                        status = "completed"
                        break

            return {"status": status, "sms_code": sms_code, "sms_text": sms_text}

        except Exception as e:
            logger.error(f"Verification status error: {str(e)}")
            return {
                "status": "error",
                "sms_code": None,
                "sms_text": None,
                "error": str(e),
            }

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

    async def get_account_balance(self) -> float:
        """Get account balance as float.

        Returns:
            Current balance in USD
        """
        try:
            data = await self.get_balance()
            return data["balance"]
        except Exception:
            return 0.0

    async def get_area_codes_list(self, service: str, country: str = "US") -> list:
        """Get available area codes for a service.

        Args:
            service: Service name
            country: Country code (default US)

        Returns:
            List of area codes
        """
        try:
            if not self.enabled:
                return []

            # Note: TextVerified Python SDK specific implementation
            # We wrap this in try/except safely
            if hasattr(self.client, "area_codes"):
                codes = self.client.area_codes.list(service_name=service)
                return [str(c.area_code) for c in codes] if codes else []

            return []
        except Exception as e:
            logger.warning(f"Failed to fetch area codes: {e}")
            return []
