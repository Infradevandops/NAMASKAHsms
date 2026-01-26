"""Unified error handling system consolidating all error handling implementations."""

import logging
from typing import Any, Callable, Dict, Optional

from fastapi import Request, Response
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError, OperationalError, SQLAlchemyError
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.middleware.base import BaseHTTPMiddleware

# from botocore.exceptions import ClientError, BotoCoreError
# # from cryptography.fernet import InvalidToken

logger = logging.getLogger(__name__)

# Unified Exception Classes


class NamaskahException(Exception):
    """Base exception class for all Namaskah errors."""

    def __init__(
        self,
        message: str,
        error_code: str = "GENERAL_ERROR",
        details: Optional[Dict[str, Any]] = None,
        status_code: int = 500,
    ):
        self.message = message
        self.error_code = error_code
        self.details = details or {}
        self.status_code = status_code
        super().__init__(self.message)


class AuthenticationError(NamaskahException):
    def __init__(
        self,
        message: str = "Authentication failed",
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message, "AUTH_ERROR", details, 401)


class AuthorizationError(NamaskahException):
    def __init__(self, message: str = "Access denied", details: Optional[Dict[str, Any]] = None):
        super().__init__(message, "AUTHZ_ERROR", details, 403)


class ValidationError(NamaskahException):
    def __init__(
        self,
        message: str = "Validation failed",
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message, "VALIDATION_ERROR", details, 400)


class ExternalServiceError(NamaskahException):
    def __init__(
        self,
        service: str,
        message: str = "External service error",
        details: Optional[Dict[str, Any]] = None,
    ):
        details = details or {}
        details["service"] = service
        super().__init__(message, "EXTERNAL_SERVICE_ERROR", details, 502)


class DatabaseError(NamaskahException):
    def __init__(
        self,
        message: str = "Database operation failed",
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message, "DATABASE_ERROR", details, 500)


class PaymentError(NamaskahException):
    def __init__(
        self,
        message: str = "Payment processing failed",
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message, "PAYMENT_ERROR", details, 402)


class InsufficientCreditsError(NamaskahException):
    def __init__(self, required_or_message, available=None):
        if available is not None:
            message = f"Insufficient credits. Required: {required_or_message}, Available: {available}"
            details = {"required": required_or_message, "available": available}
        else:
            message = str(required_or_message)
            details = {}
        super().__init__(message, "INSUFFICIENT_CREDITS", details, 402)


class VerificationError(NamaskahException):
    def __init__(
        self,
        message: str = "Verification failed",
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message, "VERIFICATION_ERROR", details, 400)


class RentalError(NamaskahException):
    def __init__(
        self,
        message: str = "Rental operation failed",
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message, "RENTAL_ERROR", details, 400)


class RateLimitError(NamaskahException):
    def __init__(
        self,
        message: str = "Rate limit exceeded",
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message, "RATE_LIMIT_ERROR", details, 429)


class ServiceUnavailableError(NamaskahException):
    def __init__(
        self,
        message: str = "Service temporarily unavailable",
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message, "SERVICE_UNAVAILABLE", details, 503)


# Unified Middleware


class UnifiedErrorHandlingMiddleware(BaseHTTPMiddleware):
    """Unified error handling middleware with fallback responses."""

    def __init__(self, app):
        super().__init__(app)
        self.fallback_responses = self._get_fallback_responses()

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Skip error handling for auth endpoints and all API endpoints
        path = str(request.url.path)
        if path.startswith("/api/") or path.startswith("/auth/"):
            return await call_next(request)

        try:
            response = await call_next(request)

            # Check for fallback if response failed
            if response.status_code >= 400:
                fallback = self._get_fallback_response(request)
                if fallback:
                    return fallback

            return response

        except Exception as exc:
            logger.error(
                "Unhandled error in %s %s: %s",
                request.method,
                request.url,
                str(exc),
                exc_info=True,
            )

            # Try fallback first
            fallback = self._get_fallback_response(request)
            if fallback:
                return fallback

            # Return appropriate error response
            return await self._handle_error(request, exc)

    def _get_fallback_response(self, request: Request) -> Optional[JSONResponse]:
        """Get fallback response for critical endpoints."""
        path = str(request.url.path)
        if path in self.fallback_responses:
            logger.warning("Using fallback response for %s", path)
            return JSONResponse(
                status_code=200,
                content=self.fallback_responses[path],
                headers={"X - Fallback-Response": "true"},
            )
        return None

    async def _handle_error(self, request: Request, exc: Exception) -> JSONResponse:
        """Handle different types of errors and return appropriate responses."""

        # Database errors
        if "database" in str(exc).lower() or "connection" in str(exc).lower():
            return JSONResponse(
                status_code=503,
                content={
                    "error": "Service temporarily unavailable",
                    "message": "Database connection issue. Please try again later.",
                    "fallback_available": True,
                },
            )

        # Network/API errors
        if "network" in str(exc).lower() or "timeout" in str(exc).lower():
            return JSONResponse(
                status_code=503,
                content={
                    "error": "External service unavailable",
                    "message": "External API is temporarily unavailable.",
                    "fallback_available": True,
                },
            )

        # Authentication errors (but not for auth endpoints)
        path = str(request.url.path)
        if (
            ("auth" in str(exc).lower() or "token" in str(exc).lower())
            and not path.startswith("/api/auth/")
            and not path.startswith("/auth/")
        ):
            return JSONResponse(
                status_code=401,
                content={
                    "error": "Authentication required",
                    "message": "Please login to continue.",
                    "redirect": "/auth/login",
                },
            )

        # Generic server error
        return JSONResponse(
            status_code=500,
            content={
                "error": "Internal server error",
                "message": "Something went wrong. Please try again later.",
            },
        )

    def _get_fallback_responses(self) -> Dict[str, Dict]:
        """Get fallback responses for critical endpoints."""
        return {
            "/verify/services": {
                "services": [
                    {
                        "id": "telegram",
                        "name": "telegram",
                        "display_name": "Telegram",
                        "price": 0.75,
                        "available": True,
                    },
                    {
                        "id": "whatsapp",
                        "name": "whatsapp",
                        "display_name": "WhatsApp",
                        "price": 0.75,
                        "available": True,
                    },
                    {
                        "id": "discord",
                        "name": "discord",
                        "display_name": "Discord",
                        "price": 0.75,
                        "available": True,
                    },
                    {
                        "id": "google",
                        "name": "google",
                        "display_name": "Google",
                        "price": 0.75,
                        "available": True,
                    },
                ]
            },
            "/countries/": {
                "countries": [
                    {
                        "code": "US",
                        "name": "United States",
                        "price_multiplier": 1.0,
                        "voice_supported": True,
                    },
                    {
                        "code": "GB",
                        "name": "United Kingdom",
                        "price_multiplier": 1.0,
                        "voice_supported": True,
                    },
                    {
                        "code": "CA",
                        "name": "Canada",
                        "price_multiplier": 1.1,
                        "voice_supported": True,
                    },
                ]
            },
            "/admin/stats": {
                "total_users": 1,
                "new_users": 0,
                "total_verifications": 0,
                "success_rate": 0.0,
                "total_spent": 0.0,
                "pending_verifications": 0,
            },
        }


# Exception Handlers


async def unified_exception_handler(request: Request, exc: NamaskahException) -> JSONResponse:
    """Handle custom Namaskah exceptions."""
    logger.error(
        "NamaskahException: %s - %s",
        exc.error_code,
        exc.message,
        extra={"details": exc.details},
    )

    return JSONResponse(
        status_code=exc.status_code,
        content=jsonable_encoder(
            {
                "error": exc.error_code,
                "message": exc.message,
                "details": exc.details,
            }
        ),
    )


async def http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    """Handle HTTP exceptions."""
    logger.warning("HTTPException: %s - %s", exc.status_code, exc.detail)

    return JSONResponse(
        status_code=exc.status_code,
        content=jsonable_encoder(
            {
                "error": "HTTP_ERROR",
                "message": exc.detail,
                "details": {"status_code": exc.status_code},
            }
        ),
    )


async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """Handle request validation errors."""
    logger.warning("ValidationError: %s", exc.errors())

    return JSONResponse(
        status_code=422,
        content=jsonable_encoder(
            {
                "error": "VALIDATION_ERROR",
                "message": "Request validation failed",
                "details": {"errors": exc.errors()},
            }
        ),
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
        error_details = {"timestamp": str(exc.__class__.__name__)}

    return JSONResponse(
        status_code=500,
        content=jsonable_encoder(
            {
                "error": "INTERNAL_ERROR",
                "message": "An unexpected error occurred",
                "details": error_details,
            }
        ),
    )


# Exception Decorators


def handle_database_exceptions(func):
    """Decorator to handle database exceptions."""

    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except IntegrityError as e:
            logger.error(f"Database integrity error in {func.__name__}: {e}")
            raise ValidationError("Data integrity constraint violated", {"original_error": str(e)})
        except OperationalError as e:
            logger.error(f"Database operational error in {func.__name__}: {e}")
            raise DatabaseError(
                "Database connection or \
    operation failed",
                {"original_error": str(e)},
            )
        except SQLAlchemyError as e:
            logger.error(f"SQLAlchemy error in {func.__name__}: {e}")
            raise DatabaseError("Database operation failed", {"original_error": str(e)})

    return wrapper


def handle_aws_exceptions(service_name: str):
    """Decorator to handle AWS service exceptions."""

    def decorator(func):
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                logger.error(f"AWS {service_name} error in {func.__name__}: {e}")
                raise ExternalServiceError(
                    service_name,
                    f"{service_name} operation failed",
                    {"original_error": str(e)},
                )

        return wrapper

    return decorator


def handle_encryption_exceptions(func):
    """Decorator to handle encryption exceptions."""

    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except ValueError as e:
            if "Invalid" in str(e) and ("key" in str(e).lower() or "token" in str(e).lower()):
                logger.error(f"Invalid encryption key/token in {func.__name__}: {e}")
                raise ValidationError("Invalid encryption key or token", {"original_error": str(e)})
            raise
        except Exception as e:
            if "token" in str(e).lower() or "decrypt" in str(e).lower():
                logger.error(f"Encryption error in {func.__name__}: {e}")
                raise ValidationError("Encryption/decryption failed", {"original_error": str(e)})
            raise

    return wrapper


def handle_http_client_exceptions(service_name: str):
    """Decorator to handle HTTP client exceptions."""

    def decorator(func):
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except ConnectionError as e:
                logger.error(f"Connection error to {service_name} in {func.__name__}: {e}")
                raise ExternalServiceError(
                    service_name,
                    f"Failed to connect to {service_name}",
                    {"original_error": str(e)},
                )
            except TimeoutError as e:
                logger.error(f"Timeout error to {service_name} in {func.__name__}: {e}")
                raise ExternalServiceError(
                    service_name,
                    f"Timeout connecting to {service_name}",
                    {"original_error": str(e)},
                )
            except Exception as e:
                if "timeout" in str(e).lower():
                    logger.error(f"Timeout error to {service_name} in {func.__name__}: {e}")
                    raise ExternalServiceError(
                        service_name,
                        f"Timeout connecting to {service_name}",
                        {"original_error": str(e)},
                    )
                elif "connection" in str(e).lower():
                    logger.error(f"Connection error to {service_name} in {func.__name__}: {e}")
                    raise ExternalServiceError(
                        service_name,
                        f"Connection error to {service_name}",
                        {"original_error": str(e)},
                    )
                raise

        return wrapper

    return decorator


# Utility Functions


def safe_int_conversion(value: str, default: int = 0, field_name: str = "value") -> int:
    """Safely convert string to int with specific error handling."""
    try:
        return int(value)
    except (ValueError, TypeError) as e:
        logger.warning(f"Failed to convert {field_name} '{value}' to int: {e}")
        return default


def safe_json_parse(json_str: str, default: dict = None, field_name: str = "data") -> dict:
    """Safely parse JSON string with specific error handling."""
    import json

    if default is None:
        default = {}

    try:
        return json.loads(json_str)
    except (json.JSONDecodeError, TypeError) as e:
        logger.warning(f"Failed to parse JSON {field_name}: {e}")
        return default


# Setup Function


def setup_unified_error_handling(app):
    """Setup unified error handling for FastAPI app."""
    # Add middleware
    app.add_middleware(UnifiedErrorHandlingMiddleware)

    # Add exception handlers
    app.add_exception_handler(NamaskahException, unified_exception_handler)
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(Exception, general_exception_handler)

    # Add custom 404 handler
    @app.exception_handler(404)
    async def not_found_handler(request: Request, exc):
        return JSONResponse(
            status_code=404,
            content={
                "error": "Not found",
                "message": "The requested resource was not found.",
                "path": str(request.url.path),
            },
        )


def setup_unified_middleware(app):
    """Setup all unified middleware for FastAPI app."""
    from app.core.unified_rate_limiting import setup_unified_rate_limiting

    # Setup rate limiting first (should be early in middleware stack)
    setup_unified_rate_limiting(app)

    # Setup error handling
    setup_unified_error_handling(app)
