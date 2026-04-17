"""Custom exception hierarchy for Namaskah SMS platform."""

from typing import Any, Dict, Optional


class NamaskahException(Exception):
    """Base exception for all Namaskah-specific errors."""

    def __init__(
        self, message: str, error_code: str = None, details: Dict[str, Any] = None
    ):
        self.message = message
        self.error_code = error_code or self.__class__.__name__
        self.details = details or {}
        super().__init__(self.message)


class ValidationError(NamaskahException):
    """Raised when input validation fails."""

    pass


class AuthenticationError(NamaskahException):
    """Raised when authentication fails."""

    pass


class AuthorizationError(NamaskahException):
    """Raised when user lacks required permissions."""

    pass


class PaymentError(NamaskahException):
    """Base class for payment-related errors."""

    pass


class InsufficientCreditsError(PaymentError):
    """Raised when user has insufficient credits."""

    def __init__(self, required: float, available: float):
        self.required = required
        self.available = available
        super().__init__(
            f"Insufficient credits. Required: ${required:.2f}, Available: ${available:.2f}",
            details={"required": required, "available": available},
        )


class PaymentProcessingError(PaymentError):
    """Raised when payment processing fails."""

    pass


class DuplicatePaymentError(PaymentError):
    """Raised when duplicate payment is detected."""

    pass


class SMSVerificationError(NamaskahException):
    """Base class for SMS verification errors."""

    pass


class ServiceUnavailableError(SMSVerificationError):
    """Raised when SMS service is unavailable."""

    pass


class NumberPurchaseError(SMSVerificationError):
    """Raised when number purchase fails."""

    pass

class AreaCodeUnavailableException(SMSVerificationError):
    """Raised when an area code is unavailable and we have alternatives."""
    def __init__(self, area_code: str, service: str, alternatives: list = None):
        self.area_code = area_code
        self.service = service
        self.alternatives = alternatives or []
        super().__init__(
            f"{area_code} is not available for {service} right now.",
            details={"area_code": area_code, "service": service, "alternatives": self.alternatives}
        )



class MessageTimeoutError(SMSVerificationError):
    """Raised when SMS message times out."""

    pass


class ExternalAPIError(NamaskahException):
    """Base class for external API errors."""

    def __init__(
        self,
        service: str,
        message: str,
        status_code: int = None,
        response_data: Dict = None,
    ):
        self.service = service
        self.status_code = status_code
        self.response_data = response_data or {}
        super().__init__(
            f"{service} API error: {message}",
            details={
                "service": service,
                "status_code": status_code,
                "response_data": response_data,
            },
        )


# Backwards-compatible alias
ExternalServiceError = ExternalAPIError


class TextVerifiedAPIError(ExternalAPIError):
    """Raised when TextVerified API fails."""

    def __init__(
        self, message: str, status_code: int = None, response_data: Dict = None
    ):
        super().__init__("TextVerified", message, status_code, response_data)


class PaystackAPIError(ExternalAPIError):
    """Raised when Paystack API fails."""

    def __init__(
        self, message: str, status_code: int = None, response_data: Dict = None
    ):
        super().__init__("Paystack", message, status_code, response_data)


class DatabaseError(NamaskahException):
    """Base class for database errors."""

    pass


class ConnectionError(DatabaseError):
    """Raised when database connection fails."""

    pass


class TransactionError(DatabaseError):
    """Raised when database transaction fails."""

    pass


class CacheError(NamaskahException):
    """Base class for cache-related errors."""

    pass


class CacheConnectionError(CacheError):
    """Raised when cache connection fails."""

    pass


class RateLimitError(NamaskahException):
    """Raised when rate limit is exceeded."""

    def __init__(self, limit: int, window: int, retry_after: int = None):
        self.limit = limit
        self.window = window
        self.retry_after = retry_after
        super().__init__(
            f"Rate limit exceeded: {limit} requests per {window} seconds",
            details={"limit": limit, "window": window, "retry_after": retry_after},
        )


class TierLimitError(NamaskahException):
    """Raised when tier limit is exceeded."""

    def __init__(self, current_tier: str, required_tier: str, feature: str):
        self.current_tier = current_tier
        self.required_tier = required_tier
        self.feature = feature
        super().__init__(
            f"Feature '{feature}' requires {required_tier} tier. Current tier: {current_tier}",
            details={
                "current_tier": current_tier,
                "required_tier": required_tier,
                "feature": feature,
            },
        )


class ConfigurationError(NamaskahException):
    """Raised when configuration is invalid."""

    pass


class SecurityError(NamaskahException):
    """Base class for security-related errors."""

    pass


class CSRFError(SecurityError):
    """Raised when CSRF validation fails."""

    pass


class TokenError(SecurityError):
    """Base class for token-related errors."""

    pass


class InvalidTokenError(TokenError):
    """Raised when token is invalid."""

    pass


class ExpiredTokenError(TokenError):
    """Raised when token has expired."""

    pass


# Error code mapping for API responses
ERROR_CODE_MAP = {
    ValidationError: "VALIDATION_ERROR",
    AuthenticationError: "AUTHENTICATION_ERROR",
    AuthorizationError: "AUTHORIZATION_ERROR",
    InsufficientCreditsError: "INSUFFICIENT_CREDITS",
    PaymentProcessingError: "PAYMENT_PROCESSING_ERROR",
    DuplicatePaymentError: "DUPLICATE_PAYMENT",
    ServiceUnavailableError: "SERVICE_UNAVAILABLE",
    NumberPurchaseError: "NUMBER_PURCHASE_ERROR",
    MessageTimeoutError: "MESSAGE_TIMEOUT",
    AreaCodeUnavailableException: "AREA_CODE_UNAVAILABLE",
    TextVerifiedAPIError: "TEXTVERIFIED_API_ERROR",
    PaystackAPIError: "PAYSTACK_API_ERROR",
    ConnectionError: "DATABASE_CONNECTION_ERROR",
    TransactionError: "DATABASE_TRANSACTION_ERROR",
    CacheConnectionError: "CACHE_CONNECTION_ERROR",
    RateLimitError: "RATE_LIMIT_EXCEEDED",
    TierLimitError: "TIER_LIMIT_EXCEEDED",
    ConfigurationError: "CONFIGURATION_ERROR",
    CSRFError: "CSRF_ERROR",
    InvalidTokenError: "INVALID_TOKEN",
    ExpiredTokenError: "EXPIRED_TOKEN",
}


def get_error_code(exception: Exception) -> str:
    """Get error code for exception."""
    return ERROR_CODE_MAP.get(type(exception), "INTERNAL_ERROR")
