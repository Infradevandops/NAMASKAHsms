"""Production TextVerified API client with circuit breaker and health checks."""
import asyncio
import time
from typing import Dict, Any, Optional
from enum import Enum
import httpx
from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)

class CircuitState(Enum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"

class TextVerifiedClient:
    """Production-ready TextVerified API client with circuit breaker."""
    
    def __init__(self):
        self.api_key = settings.textverified_api_key
        self.base_url = "https://www.textverified.com/api"
        self.timeout = 30
        self.max_retries = 3
        
        # Validate API key format
        if self.api_key and not self.api_key.startswith(('tv_', 'MSZ')):
            logger.warning("API key format may be incorrect")
        
        # Circuit breaker configuration
        self.circuit_state = CircuitState.CLOSED
        self.failure_count = 0
        self.failure_threshold = 5
        self.recovery_timeout = 60
        self.last_failure_time = 0
        
        # Health check
        self.last_health_check = 0
        self.health_check_interval = 300  # 5 minutes
        self.is_healthy = True
        
    async def health_check(self) -> bool:
        """Check API health status."""
        try:
            result = await self.make_request("GetBalance")
            self.is_healthy = "error" not in result
            return self.is_healthy
        except Exception as e:
            logger.warning("Health check failed: %s", e)
            self.is_healthy = False
            return False
        
    def _reset_circuit(self):
        """Reset circuit breaker to closed state."""
        self.circuit_state = CircuitState.CLOSED
        self.failure_count = 0
        
    def _record_failure(self):
        """Record API failure and update circuit state."""
        self.failure_count += 1
        self.last_failure_time = time.time()
        
        if self.failure_count >= self.failure_threshold:
            self.circuit_state = CircuitState.OPEN
            logger.warning("Circuit breaker opened due to failures")
            
    def _can_attempt_request(self) -> bool:
        """Check if request can be attempted based on circuit state."""
        if self.circuit_state == CircuitState.CLOSED:
            return True
            
        if self.circuit_state == CircuitState.OPEN:
            if time.time() - self.last_failure_time > self.recovery_timeout:
                self.circuit_state = CircuitState.HALF_OPEN
                logger.info("Circuit breaker half-open, attempting recovery")
                return True
            return False
            
        return True  # HALF_OPEN
        
    async def make_request(self, endpoint: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
        """Make API request with correct TextVerified authentication."""
        if not self._can_attempt_request():
            return {"error": "Circuit breaker open - service temporarily unavailable"}
            
        # TextVerified API uses 'bearer' parameter for authentication
        request_params = {"bearer": self.api_key}
        if params:
            request_params.update(params)
            
        # Add User-Agent header to avoid redirects
        headers = {
            "User-Agent": "Namaskah-SMS/1.0",
            "Accept": "application/json, text/plain"
        }
            
        for attempt in range(self.max_retries):
            try:
                async with httpx.AsyncClient(timeout=self.timeout, follow_redirects=True) as client:
                    url = f"{self.base_url}/{endpoint}"
                    logger.info("Making request to %s", url)
                    
                    response = await client.get(
                        url,
                        params=request_params,
                        headers=headers
                    )
                    
                    logger.info("Response status: %s", response.status_code)
                    
                    if response.status_code == 200:
                        try:
                            # TextVerified may return plain text or JSON
                            response_text = response.text.strip()
                            
                            # Try to parse as JSON first
                            try:
                                data = response.json()
                                logger.info(f"API success: {endpoint}")
                                self._reset_circuit()  # Reset on success
                                return data
                            except:
                                # Handle plain text responses
                                if response_text.startswith("ERROR:"):
                                    error_msg = response_text.replace("ERROR:", "").strip()
                                    logger.error("API error: %s", error_msg)
                                    self._record_failure()
                                    return {"error": error_msg}
                                else:
                                    # Success response in plain text
                                    logger.info(f"API success: {endpoint} - {response_text}")
                                    self._reset_circuit()
                                    return self._parse_text_response(endpoint, response_text)
                                    
                        except Exception as e:
                            logger.error("Failed to parse response: %s", e)
                            self._record_failure()
                            return {"error": "Invalid response format"}
                        
                    elif response.status_code == 401:
                        logger.error("Invalid API key - Status 401")
                        self._record_failure()
                        return {"error": "Invalid API key"}
                        
                    elif response.status_code == 429:
                        wait_time = 2 ** attempt
                        logger.warning("Rate limited, waiting %ss", wait_time)
                        await asyncio.sleep(wait_time)
                        continue
                        
                    else:
                        error_text = response.text
                        logger.error("API error %s: %s", response.status_code, error_text)
                        self._record_failure()
                        return {"error": f"API error {response.status_code}: {error_text}"}
                        
            except (httpx.TimeoutException, httpx.ConnectError) as e:
                logger.warning("Request failed (attempt %s): %s", attempt + 1, e)
                self._record_failure()
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(2 ** attempt)
                    
            except Exception as e:
                logger.error("Unexpected error: %s", e)
                self._record_failure()
                return {"error": f"Request error: {str(e)}"}
                
        return {"error": "API request failed after all retries"}
    
    def _parse_text_response(self, endpoint: str, response_text: str) -> Dict[str, Any]:
        """Parse TextVerified plain text responses."""
        if endpoint == "GetBalance":
            try:
                balance = float(response_text)
                return {"balance": balance, "currency": "USD"}
            except ValueError:
                return {"error": "Invalid balance format"}
                
        elif endpoint == "GetNumber" or "GetNumber" in endpoint:
            # Format: "id:phone_number" or just "phone_number"
            if ";" in response_text:
                parts = response_text.split(";")
                return {"id": parts[0], "number": parts[1] if len(parts) > 1 else parts[0]}
            else:
                return {"id": response_text, "number": response_text}
                
        elif "GetSMS" in endpoint or "GetVoice" in endpoint:
            # SMS/Voice code response
            if response_text and response_text != "NO_SMS":
                return {"sms" if "SMS" in endpoint else "voice": response_text}
            else:
                return {"error": "No message received yet"}
                
        elif "Cancel" in endpoint:
            if response_text == "ACCESS_CANCEL":
                return {"success": True}
            else:
                return {"error": response_text}
                
        else:
            # Generic response
            return {"response": response_text}

    async def get_verification_status(self, verification_id: str) -> Dict[str, Any]:
        """Get verification status by ID."""
        return await self.make_request(f"GetStatus/{verification_id}")

# Global client instance
textverified_client = TextVerifiedClient()