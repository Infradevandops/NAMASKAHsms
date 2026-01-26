"""Comprehensive error handling and retry logic."""

import asyncio
from functools import wraps
from typing import Any, Callable, Optional, TypeVar

import httpx

from app.core.logging import get_logger

logger = get_logger(__name__)

T = TypeVar("T")


class RetryConfig:
    """Configuration for retry logic."""

    def __init__(
        self,
        max_retries: int = 3,
        initial_delay: float = 1.0,
        max_delay: float = 60.0,
        exponential_base: float = 2.0,
    ):
        self.max_retries = max_retries
        self.initial_delay = initial_delay
        self.max_delay = max_delay
        self.exponential_base = exponential_base

    def get_delay(self, attempt: int) -> float:
        """Calculate delay with exponential backoff."""
        delay = self.initial_delay * (self.exponential_base**attempt)
        return min(delay, self.max_delay)


def retry_with_backoff(config: Optional[RetryConfig] = None):
    """Decorator for retry logic with exponential backoff."""
    if config is None:
        config = RetryConfig()

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        @wraps(func)
        async def async_wrapper(*args, **kwargs) -> Any:
            last_exception = None

            for attempt in range(config.max_retries):
                try:
                    return await func(*args, **kwargs)
                except (httpx.HTTPError, asyncio.TimeoutError) as e:
                    last_exception = e
                    if attempt < config.max_retries - 1:
                        delay = config.get_delay(attempt)
                        logger.warning(
                            f"Attempt {attempt + 1} failed for {func.__name__}, " f"retrying in {delay}s: {str(e)}"
                        )
                        await asyncio.sleep(delay)
                    else:
                        logger.error(f"All {config.max_retries} attempts failed for {func.__name__}: {str(e)}")

            raise last_exception or Exception(f"Failed after {config.max_retries} attempts")

        @wraps(func)
        def sync_wrapper(*args, **kwargs) -> Any:
            last_exception = None

            for attempt in range(config.max_retries):
                try:
                    return func(*args, **kwargs)
                except (httpx.HTTPError, Exception) as e:
                    last_exception = e
                    if attempt < config.max_retries - 1:
                        delay = config.get_delay(attempt)
                        logger.warning(
                            f"Attempt {attempt + 1} failed for {func.__name__}, " f"retrying in {delay}s: {str(e)}"
                        )
                        asyncio.run(asyncio.sleep(delay))
                    else:
                        logger.error(f"All {config.max_retries} attempts failed for {func.__name__}: {str(e)}")

            raise last_exception or Exception(f"Failed after {config.max_retries} attempts")

        # Return async wrapper if function is async
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper

    return decorator


class APIErrorHandler:
    """Handle API errors with user-friendly messages."""

    ERROR_MESSAGES = {
        401: "Authentication failed. Please check your API credentials.",
        400: "Invalid request. Please check your input parameters.",
        404: "Resource not found.",
        429: "Rate limit exceeded. Please try again later.",
        500: "Server error. Please try again later.",
        503: "Service temporarily unavailable. Please try again later.",
    }

    @staticmethod
    def get_user_message(status_code: int, error: str = "") -> str:
        """Get user-friendly error message."""
        message = APIErrorHandler.ERROR_MESSAGES.get(status_code, "An error occurred. Please try again.")
        if error:
            message = f"{message} ({error})"
        return message

    @staticmethod
    def is_retryable(status_code: int) -> bool:
        """Check if error is retryable."""
        return status_code in [429, 500, 502, 503, 504]

    @staticmethod
    def log_error(
        error_type: str,
        status_code: Optional[int] = None,
        message: str = "",
        context: Optional[dict] = None,
    ):
        """Log error with context."""
        log_data = {
            "error_type": error_type,
            "status_code": status_code,
            "message": message,
        }
        if context:
            log_data.update(context)

        logger.error(f"API Error: {log_data}")
