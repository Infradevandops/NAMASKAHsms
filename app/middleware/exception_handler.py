"""Comprehensive exception handling middleware."""

import traceback
import uuid
from typing import Callable, Optional
from datetime import datetime

from fastapi import Request, status
from fastapi.responses import JSONResponse
from pydantic import ValidationError
from sqlalchemy.exc import SQLAlchemyError
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.logging import get_logger
from app.core.error_responses import (
    ErrorCode,
    ErrorResponse,
    create_error_response,
    get_http_status_code,
)

logger = get_logger(__name__)


class AppException(Exception):
    """Base application exception."""

    def __init__(
        self,
        message: str,
        code: ErrorCode = ErrorCode.INTERNAL_ERROR,
        details: Optional[list] = None,
        status_code: Optional[int] = None,
    ):
        self.message = message
        self.code = code
        self.details = details or []
        self.status_code = status_code or get_http_status_code(code)
        super().__init__(self.message)


class ValidationException(AppException):
    """Validation error exception."""

    def __init__(self, message: str, details: Optional[list] = None):
        super().__init__(
            message=message, code=ErrorCode.VALIDATION_ERROR, details=details, status_code=400
        )


class AuthenticationException(AppException):
    """Authentication error exception."""

    def __init__(self, message: str = "Authentication failed"):
        super().__init__(message=message, code=ErrorCode.UNAUTHORIZED, status_code=401)


class AuthorizationException(AppException):
    """Authorization error exception."""

    def __init__(self, message: str = "Insufficient permissions"):
        super().__init__(message=message, code=ErrorCode.FORBIDDEN, status_code=403)


class ResourceNotFoundException(AppException):
    """Resource not found exception."""

    def __init__(self, resource: str = "Resource"):
        super().__init__(message=f"{resource} not found", code=ErrorCode.NOT_FOUND, status_code=404)


class ConflictException(AppException):
    """Conflict exception."""

    def __init__(self, message: str = "Resource already exists"):
        super().__init__(message=message, code=ErrorCode.CONFLICT, status_code=409)


class RateLimitException(AppException):
    """Rate limit exceeded exception."""

    def __init__(self, message: str = "Too many requests"):
        super().__init__(message=message, code=ErrorCode.RATE_LIMIT_EXCEEDED, status_code=429)


class InsufficientCreditsException(AppException):
    """Insufficient credits exception."""

    def __init__(self, message: str = "Insufficient credits"):
        super().__init__(message=message, code=ErrorCode.INSUFFICIENT_CREDITS, status_code=402)


class ExceptionHandlerMiddleware(BaseHTTPMiddleware):
    """Middleware for handling exceptions and converting to standardized responses."""

    async def dispatch(self, request: Request, call_next: Callable) -> JSONResponse:
        """Handle exceptions in request processing."""
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id

        try:
            response = await call_next(request)
            return response

        except ValidationError as e:
            """Handle Pydantic validation errors."""
            logger.warning(
                f"Validation error in {request.method} {request.url.path}",
                extra={"request_id": request_id, "errors": e.errors()},
            )

            details = []
            for error in e.errors():
                details.append(
                    {
                        "field": ".".join(str(x) for x in error.get("loc", [])),
                        "message": error.get("msg", "Validation failed"),
                        "code": "INVALID_FORMAT",
                    }
                )

            error_response = create_error_response(
                error_type="Validation Error",
                code=ErrorCode.VALIDATION_ERROR,
                message="Request validation failed",
                details=details,
                request_id=request_id,
            )

            return JSONResponse(status_code=400, content=error_response.dict())

        except AppException as e:
            """Handle application exceptions."""
            logger.warning(
                f"Application error in {request.method} {request.url.path}: {e.message}",
                extra={"request_id": request_id, "code": e.code.value},
            )

            error_response = create_error_response(
                error_type=e.code.name.replace("_", " ").title(),
                code=e.code,
                message=e.message,
                details=e.details,
                request_id=request_id,
            )

            return JSONResponse(status_code=e.status_code, content=error_response.dict())

        except SQLAlchemyError as e:
            """Handle database errors."""
            logger.error(
                f"Database error in {request.method} {request.url.path}",
                extra={"request_id": request_id, "error": str(e)},
                exc_info=True,
            )

            error_response = create_error_response(
                error_type="Database Error",
                code=ErrorCode.DATABASE_ERROR,
                message="Database operation failed",
                request_id=request_id,
            )

            return JSONResponse(status_code=500, content=error_response.dict())

        except ValueError as e:
            """Handle value errors."""
            logger.warning(
                f"Value error in {request.method} {request.url.path}: {str(e)}",
                extra={"request_id": request_id},
            )

            error_response = create_error_response(
                error_type="Validation Error",
                code=ErrorCode.INVALID_INPUT,
                message=str(e),
                request_id=request_id,
            )

            return JSONResponse(status_code=400, content=error_response.dict())

        except KeyError as e:
            """Handle missing key errors."""
            logger.warning(
                f"Missing key error in {request.method} {request.url.path}: {str(e)}",
                extra={"request_id": request_id},
            )

            error_response = create_error_response(
                error_type="Validation Error",
                code=ErrorCode.MISSING_FIELD,
                message=f"Missing required field: {str(e)}",
                request_id=request_id,
            )

            return JSONResponse(status_code=400, content=error_response.dict())

        except AttributeError as e:
            """Handle attribute errors."""
            logger.error(
                f"Attribute error in {request.method} {request.url.path}: {str(e)}",
                extra={"request_id": request_id},
                exc_info=True,
            )

            error_response = create_error_response(
                error_type="Internal Error",
                code=ErrorCode.INTERNAL_ERROR,
                message="An internal error occurred",
                request_id=request_id,
            )

            return JSONResponse(status_code=500, content=error_response.dict())

        except TypeError as e:
            """Handle type errors."""
            logger.error(
                f"Type error in {request.method} {request.url.path}: {str(e)}",
                extra={"request_id": request_id},
                exc_info=True,
            )

            error_response = create_error_response(
                error_type="Validation Error",
                code=ErrorCode.INVALID_FORMAT,
                message="Invalid data type",
                request_id=request_id,
            )

            return JSONResponse(status_code=400, content=error_response.dict())

        except Exception as e:
            """Handle all other exceptions."""
            logger.error(
                f"Unhandled exception in {request.method} {request.url.path}: {str(e)}",
                extra={"request_id": request_id},
                exc_info=True,
            )

            # Log full traceback for debugging
            logger.debug(f"Traceback: {traceback.format_exc()}")

            error_response = create_error_response(
                error_type="Internal Error",
                code=ErrorCode.INTERNAL_ERROR,
                message="An unexpected error occurred",
                request_id=request_id,
            )

            return JSONResponse(status_code=500, content=error_response.dict())


def setup_exception_handlers(app):
    """Setup exception handlers for FastAPI app."""

    @app.exception_handler(AppException)
    async def app_exception_handler(request: Request, exc: AppException):
        """Handle application exceptions."""
        request_id = getattr(request.state, "request_id", str(uuid.uuid4()))

        error_response = create_error_response(
            error_type=exc.code.name.replace("_", " ").title(),
            code=exc.code,
            message=exc.message,
            details=exc.details,
            request_id=request_id,
        )

        return JSONResponse(status_code=exc.status_code, content=error_response.dict())

    @app.exception_handler(ValidationError)
    async def validation_exception_handler(request: Request, exc: ValidationError):
        """Handle Pydantic validation errors."""
        request_id = getattr(request.state, "request_id", str(uuid.uuid4()))

        details = []
        for error in exc.errors():
            details.append(
                {
                    "field": ".".join(str(x) for x in error.get("loc", [])),
                    "message": error.get("msg", "Validation failed"),
                    "code": "INVALID_FORMAT",
                }
            )

        error_response = create_error_response(
            error_type="Validation Error",
            code=ErrorCode.VALIDATION_ERROR,
            message="Request validation failed",
            details=details,
            request_id=request_id,
        )

        return JSONResponse(status_code=400, content=error_response.dict())

    @app.exception_handler(Exception)
    async def general_exception_handler(request: Request, exc: Exception):
        """Handle all other exceptions."""
        request_id = getattr(request.state, "request_id", str(uuid.uuid4()))

        logger.error(
            f"Unhandled exception: {str(exc)}", extra={"request_id": request_id}, exc_info=True
        )

        error_response = create_error_response(
            error_type="Internal Error",
            code=ErrorCode.INTERNAL_ERROR,
            message="An unexpected error occurred",
            request_id=request_id,
        )

        return JSONResponse(status_code=500, content=error_response.dict())
