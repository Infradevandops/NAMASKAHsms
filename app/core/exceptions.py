"""Custom exception classes and handlers for the application."""
import logging
from typing import Any, Dict, Optional

from fastapi import Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

logger = logging.getLogger(__name__)


class NamaskahException(Exception):
    """Base exception class for Namaskah application."""

    def __init__(
        self,
        message: str,
        error_code: str = "GENERAL_ERROR",
        details: Optional[Dict[str, Any]] = None,
    ):
        self.message = message
        self.error_code = error_code
        self.details = details or {}
        super().__init__(self.message)


class AuthenticationError(NamaskahException):
    """Authentication related errors."""

    def __init__(
        self,
        message: str = "Authentication failed",
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message, "AUTH_ERROR", details)


class AuthorizationError(NamaskahException):
    """Authorization related errors."""

    def __init__(
        self, message: str = "Access denied", details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message, "AUTHZ_ERROR", details)


class ValidationError(NamaskahException):
    """Data validation errors."""

    def __init__(
        self,
        message: str = "Validation failed",
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message, "VALIDATION_ERROR", details)


class ExternalServiceError(NamaskahException):
    """External service integration errors."""

    def __init__(
        self,
        service: str,
        message: str = "External service error",
        details: Optional[Dict[str, Any]] = None,
    ):
        details = details or {}
        details["service"] = service
        super().__init__(message, "EXTERNAL_SERVICE_ERROR", details)


class PaymentError(NamaskahException):
    """Payment processing errors."""

    def __init__(
        self,
        message: str = "Payment processing failed",
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message, "PAYMENT_ERROR", details)


class InsufficientCreditsError(NamaskahException):
    """Insufficient credits error."""

    def __init__(self, required_or_message, available=None):
        if available is not None:
            # Called with (required, available)
            message = f"Insufficient credits. Required: {required_or_message}, Available: {available}"
            details = {"required": required_or_message, "available": available}
        else:
            # Called with just message
            message = str(required_or_message)
            details = {}
        super().__init__(message, "INSUFFICIENT_CREDITS", details)


class VerificationError(NamaskahException):
    """SMS verification related errors."""

    def __init__(
        self,
        message: str = "Verification failed",
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message, "VERIFICATION_ERROR", details)


class RentalNotFoundError(NamaskahException):
    """Rental not found error."""

    def __init__(
        self,
        message: str = "Rental not found",
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message, "RENTAL_NOT_FOUND", details)


class RentalExpiredError(NamaskahException):
    """Rental expired error."""

    def __init__(
        self,
        message: str = "Rental has expired",
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message, "RENTAL_EXPIRED", details)

# Exception handlers


async def namaskah_exception_handler(
    request: Request, exc: NamaskahException
) -> JSONResponse:
    """Handle custom Namaskah exceptions."""
    logger.error(
        "NamaskahException: %s - %s",
        exc.error_code,
        exc.message,
        extra={"details": exc.details},
    )

    # Map exception types to HTTP status codes
    status_map = {
        "AUTH_ERROR": status.HTTP_401_UNAUTHORIZED,
        "AUTHZ_ERROR": status.HTTP_403_FORBIDDEN,
        "VALIDATION_ERROR": status.HTTP_400_BAD_REQUEST,
        "EXTERNAL_SERVICE_ERROR": status.HTTP_502_BAD_GATEWAY,
        "PAYMENT_ERROR": status.HTTP_402_PAYMENT_REQUIRED,
        "INSUFFICIENT_CREDITS": status.HTTP_402_PAYMENT_REQUIRED,
        "VERIFICATION_ERROR": status.HTTP_400_BAD_REQUEST,
        "RENTAL_NOT_FOUND": status.HTTP_404_NOT_FOUND,
        "RENTAL_EXPIRED": status.HTTP_410_GONE,
    }

    status_code = status_map.get(exc.error_code, status.HTTP_500_INTERNAL_SERVER_ERROR)

    return JSONResponse(
        status_code=status_code,
        content={
            "error": exc.error_code,
            "message": exc.message,
            "details": exc.details,
        },
    )


async def http_exception_handler(
    request: Request, exc: StarletteHTTPException
) -> JSONResponse:
    """Handle HTTP exceptions."""
    logger.warning("HTTPException: %s - %s", exc.status_code, exc.detail)

    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": "HTTP_ERROR",
            "message": exc.detail,
            "details": {"status_code": exc.status_code},
        },
    )


async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    """Handle request validation errors."""
    logger.warning("ValidationError: %s", exc.errors())

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": "VALIDATION_ERROR",
            "message": "Request validation failed",
            "details": {"errors": exc.errors()},
        },
    )


async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle unexpected exceptions."""
    logger.error("Unexpected error: %s", str(exc), exc_info=True)

    from app.core.config import get_settings

    settings = get_settings()

    # Only show detailed error info in development
    if settings.environment == "development":
        error_details = {
            "exception_type": type(exc).__name__,
            "exception_message": str(exc),
            "request_url": str(request.url),
            "request_method": request.method,
        }
    else:
        # In production, only show generic error
        error_details = {
            "timestamp": str(exc.__class__.__name__),  # Safe identifier for tracking
        }

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "INTERNAL_ERROR",
            "message": "An unexpected error occurred",
            "details": error_details,
        },
    )


def setup_exception_handlers(app):
    """Setup exception handlers for FastAPI app."""
    app.add_exception_handler(NamaskahException, namaskah_exception_handler)
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(Exception, general_exception_handler)
