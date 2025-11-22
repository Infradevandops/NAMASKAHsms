"""Unified provider base with retry logic and health checks."""
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from enum import Enum
from datetime import datetime, timedelta
import asyncio
from app.core.logging import get_logger

logger = get_logger(__name__)


class ProviderStatus(str, Enum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


class RetryConfig:
    """Retry configuration for provider operations."""

    def __init__(
        self,
        max_retries: int = 3,
        initial_delay: float = 1.0,
        max_delay: float = 10.0,
        exponential_base: float = 2.0,
        retryable_exceptions: tuple = (Exception,)
    ):
        self.max_retries = max_retries
        self.initial_delay = initial_delay
        self.max_delay = max_delay
        self.exponential_base = exponential_base
        self.retryable_exceptions = retryable_exceptions

    def get_delay(self, attempt: int) -> float:
        """Calculate delay for exponential backoff."""
        delay = self.initial_delay * (self.exponential_base ** attempt)
        return min(delay, self.max_delay)


class ProviderHealthCheck:
    """Health check tracking for providers."""

    def __init__(self, check_interval: int = 300):
        self.check_interval = check_interval
        self.last_check: Optional[datetime] = None
        self.status = ProviderStatus.UNKNOWN
        self.consecutive_failures = 0
        self.last_error: Optional[str] = None

    def mark_success(self):
        """Mark a successful health check."""
        self.status = ProviderStatus.HEALTHY
        self.consecutive_failures = 0
        self.last_check = datetime.utcnow()
        self.last_error = None

    def mark_failure(self, error: str):
        """Mark a failed health check."""
        self.consecutive_failures += 1
        self.last_check = datetime.utcnow()
        self.last_error = error

        if self.consecutive_failures >= 3:
            self.status = ProviderStatus.UNHEALTHY
        else:
            self.status = ProviderStatus.DEGRADED

    def should_check(self) -> bool:
        """Check if health check is needed."""
        if self.last_check is None:
            return True
        return datetime.utcnow() - self.last_check > timedelta(seconds=self.check_interval)

    def is_available(self) -> bool:
        """Check if provider is available for use."""
        return self.status in [ProviderStatus.HEALTHY, ProviderStatus.DEGRADED]


class UnifiedProviderBase(ABC):
    """Unified base class for all SMS providers."""

    def __init__(self, name: str, retry_config: Optional[RetryConfig] = None):
        self.name = name
        self.enabled = False
        self.retry_config = retry_config or RetryConfig()
        self.health = ProviderHealthCheck()
        self.cost_multiplier = 1.0  # For cost optimization

    @abstractmethod
    async def get_balance(self) -> Dict[str, Any]:
        """Get account balance."""

    @abstractmethod
    async def buy_number(self, country: str, service: str) -> Dict[str, Any]:
        """Purchase phone number."""

    @abstractmethod
    async def check_sms(self, activation_id: str) -> Dict[str, Any]:
        """Check for SMS messages."""

    @abstractmethod
    async def get_pricing(self, country: str, service: str) -> Dict[str, Any]:
        """Get service pricing."""

    async def health_check(self) -> bool:
        """Perform health check on provider."""
        if not self.health.should_check():
            return self.health.is_available()

        try:
            balance = await self.get_balance()
            if balance and "balance" in balance:
                self.health.mark_success()
                logger.info(f"{self.name} health check passed")
                return True
        except Exception as e:
            self.health.mark_failure(str(e))
            logger.warning(f"{self.name} health check failed: {e}")
            return False

        return False

    async def execute_with_retry(self, operation, *args, **kwargs):
        """Execute operation with retry logic."""
        last_exception = None

        for attempt in range(self.retry_config.max_retries):
            try:
                return await operation(*args, **kwargs)
            except self.retry_config.retryable_exceptions as e:
                last_exception = e
                if attempt < self.retry_config.max_retries - 1:
                    delay = self.retry_config.get_delay(attempt)
                    logger.warning(
                        f"{self.name} attempt {attempt + 1} failed, retrying in {delay}s: {e}"
                    )
                    await asyncio.sleep(delay)
                else:
                    logger.error(f"{self.name} all {self.retry_config.max_retries} attempts failed")

        raise last_exception or Exception(f"{self.name} operation failed after retries")

    def set_cost_multiplier(self, multiplier: float):
        """Set cost multiplier for optimization."""
        self.cost_multiplier = max(0.1, min(2.0, multiplier))

    def apply_cost_optimization(self, base_cost: float) -> float:
        """Apply cost optimization multiplier."""
        return base_cost * self.cost_multiplier
