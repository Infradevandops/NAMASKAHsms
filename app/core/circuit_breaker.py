"""Circuit breaker for external API calls."""


import time
from typing import Any, Callable
from app.core.logging import get_logger

logger = get_logger(__name__)


class CircuitBreaker:

    """Circuit breaker pattern implementation."""

def __init__(

        self,
        failure_threshold: int = 5,
        recovery_timeout: int = 60,
        expected_exception: type = Exception,
    ):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.expected_exception = expected_exception
        self.failure_count = 0
        self.last_failure_time = None
        self.state = "closed"  # closed, open, half_open

def call(self, func: Callable, *args, **kwargs) -> Any:

        """Execute function with circuit breaker protection."""

if self.state == "open":
if time.time() - self.last_failure_time > self.recovery_timeout:
                self.state = "half_open"
                logger.info("Circuit breaker entering half-open state")
else:
                raise Exception("Circuit breaker is OPEN - service unavailable")

try:
            result = func(*args, **kwargs)
            self._on_success()
            return result
except self.expected_exception as e:
            self._on_failure()
            raise e

def _on_success(self):

        """Handle successful call."""
if self.state == "half_open":
            self.state = "closed"
            self.failure_count = 0
            logger.info("Circuit breaker closed - service recovered")

def _on_failure(self):

        """Handle failed call."""
        self.failure_count += 1
        self.last_failure_time = time.time()

if self.failure_count >= self.failure_threshold:
            self.state = "open"
            logger.error(f"Circuit breaker OPEN - {self.failure_count} failures detected")


# Global circuit breaker for TextVerified API
textverified_circuit_breaker = CircuitBreaker(
    failure_threshold=5,
    recovery_timeout=60,
    expected_exception=Exception,
)