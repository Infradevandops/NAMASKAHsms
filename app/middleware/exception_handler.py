"""Enhanced exception handling middleware with structured logging."""

import traceback
import uuid
from typing import Callable, Optional

from fastapi import Request
from fastapi.responses import JSONResponse
from pydantic import ValidationError
from sqlalchemy.exc import SQLAlchemyError
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.exceptions import (
    DatabaseError,
    ExternalAPIError,
    NamaskahException,
    PaymentError,
    SMSVerificationError,
    get_error_code,
)
from app.core.logging import get_logger

logger = get_logger(__name__)


class ExceptionHandlerMiddleware(BaseHTTPMiddleware):
    """Enhanced middleware for handling exceptions with structured logging."""

    async def dispatch(self, request: Request, call_next: Callable) -> JSONResponse:
        """Handle exceptions with comprehensive logging and error recovery."""
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id

        # Add request context for logging
        log_context = {
            "request_id": request_id,
            "method": request.method,
            "path": request.url.path,
            "user_agent": request.headers.get("user-agent", "unknown"),
        }

        try:
            response = await call_next(request)
            return response

        except NamaskahException as e:
            # Handle custom application exceptions
            logger.warning(
                f"Application error: {e.message}",
                extra={**log_context, "error_code": e.error_code, "details": e.details},
            )

            status_code = self._get_status_code_for_exception(e)

            return JSONResponse(
                status_code=status_code,
                content={
                    "error": {
                        "type": e.__class__.__name__,
                        "code": e.error_code,
                        "message": e.message,
                        "details": e.details,
                        "request_id": request_id,
                    }
                },
            )

        except ValidationError as e:
            # Handle Pydantic validation errors
            logger.warning(
                "Validation error",
                extra={**log_context, "validation_errors": e.errors()},
            )

            details = []
            for error in e.errors():
                details.append(
                    {
                        "field": ".".join(str(x) for x in error.get("loc", [])),
                        "message": error.get("msg", "Validation failed"),
                        "type": error.get("type", "validation_error"),
                    }
                )

            return JSONResponse(
                status_code=400,
                content={
                    "error": {
                        "type": "ValidationError",
                        "code": "VALIDATION_ERROR",
                        "message": "Request validation failed",
                        "details": details,
                        "request_id": request_id,
                    }
                },
            )

        except SQLAlchemyError as e:
            # Handle database errors
            logger.error(
                "Database error",
                extra={**log_context, "db_error": str(e)},
                exc_info=True,
            )

            return JSONResponse(
                status_code=500,
                content={
                    "error": {
                        "type": "DatabaseError",
                        "code": "DATABASE_ERROR",
                        "message": "Database operation failed",
                        "request_id": request_id,
                    }
                },
            )

        except ValueError as e:
            # Handle value errors (often from invalid input)
            logger.warning(f"Value error: {str(e)}", extra=log_context)

            return JSONResponse(
                status_code=400,
                content={
                    "error": {
                        "type": "ValueError",
                        "code": "INVALID_INPUT",
                        "message": str(e),
                        "request_id": request_id,
                    }
                },
            )

        except KeyError as e:
            # Handle missing required fields
            logger.warning(f"Missing required field: {str(e)}", extra=log_context)

            return JSONResponse(
                status_code=400,
                content={
                    "error": {
                        "type": "KeyError",
                        "code": "MISSING_FIELD",
                        "message": f"Missing required field: {str(e)}",
                        "request_id": request_id,
                    }
                },
            )

        except Exception as e:
            # Handle all other unexpected exceptions
            logger.error(
                f"Unhandled exception: {str(e)}",
                extra={**log_context, "exception_type": type(e).__name__},
                exc_info=True,
            )

            # Log full traceback for debugging
            logger.debug(f"Full traceback: {traceback.format_exc()}")

            return JSONResponse(
                status_code=500,
                content={
                    "error": {
                        "type": "InternalError",
                        "code": "INTERNAL_ERROR",
                        "message": "An unexpected error occurred",
                        "request_id": request_id,
                    }
                },
            )

    def _get_status_code_for_exception(self, exc: NamaskahException) -> int:
        """Get appropriate HTTP status code for custom exceptions."""
        if isinstance(exc, PaymentError):
            if "insufficient" in exc.message.lower():
                return 402  # Payment Required
            elif "duplicate" in exc.message.lower():
                return 409  # Conflict
            else:
                return 400  # Bad Request
        elif isinstance(exc, SMSVerificationError):
            if "unavailable" in exc.message.lower():
                return 503  # Service Unavailable
            elif "timeout" in exc.message.lower():
                return 408  # Request Timeout
            else:
                return 400  # Bad Request
        elif isinstance(exc, ExternalAPIError):
            return 502  # Bad Gateway
        elif isinstance(exc, DatabaseError):
            return 500  # Internal Server Error
        elif "authentication" in exc.error_code.lower():
            return 401  # Unauthorized
        elif "authorization" in exc.error_code.lower():
            return 403  # Forbidden
        elif "validation" in exc.error_code.lower():
            return 400  # Bad Request
        elif "rate_limit" in exc.error_code.lower():
            return 429  # Too Many Requests
        else:
            return 500  # Internal Server Error
