"""Common utility functions to reduce code duplication across the codebase."""

import re
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Union

from sqlalchemy.orm import Session

from app.core.exceptions import AuthorizationError, ValidationError
from app.core.logging import get_logger
from app.schemas.responses import (create_error_response,
                                   create_paginated_response,
                                   create_success_response)

logger = get_logger(__name__)


class ValidationUtils:
    """Common validation utilities."""

    @staticmethod
    def validate_uuid(value: str, field_name: str = "ID") -> str:
        """Validate UUID format."""
        if not value:
            raise ValidationError(f"{field_name} is required")

        try:
            uuid.UUID(value)
            return value
        except ValueError:
            raise ValidationError(f"Invalid {field_name} format")

    @staticmethod
    def validate_email(email: str) -> str:
        """Validate email format."""
        if not email:
            raise ValidationError("Email is required")

        pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
        if not re.match(pattern, email):
            raise ValidationError("Invalid email format")

        return email.lower().strip()

    @staticmethod
    def validate_phone_number(phone: str) -> str:
        """Validate phone number format."""
        if not phone:
            raise ValidationError("Phone number is required")

        # Remove all non-digit characters
        digits_only = re.sub(r"\D", "", phone)

        # Check if it's a valid US number (10 or 11 digits)
        if len(digits_only) == 10:
            return f"+1{digits_only}"
        elif len(digits_only) == 11 and digits_only.startswith("1"):
            return f"+{digits_only}"
        else:
            raise ValidationError("Invalid phone number format")

    @staticmethod
    def validate_amount(amount: Union[str, float], min_amount: float = 0.01) -> float:
        """Validate monetary amount."""
        try:
            amount_float = float(amount)
            if amount_float < min_amount:
                raise ValidationError(f"Amount must be at least ${min_amount:.2f}")
            return round(amount_float, 2)
        except (ValueError, TypeError):
            raise ValidationError("Invalid amount format")


class DatabaseUtils:
    """Common database operation utilities."""

    @staticmethod
    def get_user_by_id(db: Session, user_id: str, require_active: bool = True):
        """Get user by ID with common validation."""
        from app.models.user import User

        ValidationUtils.validate_uuid(user_id, "User ID")

        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise ValidationError("User not found")

        if require_active and not user.is_active:
            raise AuthorizationError("User account is inactive")

        return user

    @staticmethod
    def get_verification_by_id(db: Session, verification_id: str, user_id: str = None):
        """Get verification by ID with optional user validation."""
        from app.models.verification import Verification

        ValidationUtils.validate_uuid(verification_id, "Verification ID")

        query = db.query(Verification).filter(Verification.id == verification_id)

        if user_id:
            ValidationUtils.validate_uuid(user_id, "User ID")
            query = query.filter(Verification.user_id == user_id)

        verification = query.first()
        if not verification:
            raise ValidationError("Verification not found")

        return verification

    @staticmethod
    def paginate_query(
        query, page: int = 1, per_page: int = 20, max_per_page: int = 100
    ):
        """Apply pagination to SQLAlchemy query."""
        if page < 1:
            page = 1
        if per_page < 1:
            per_page = 20
        if per_page > max_per_page:
            per_page = max_per_page

        total = query.count()
        items = query.offset((page - 1) * per_page).limit(per_page).all()

        return {
            "items": items,
            "total": total,
            "page": page,
            "per_page": per_page,
            "pages": (total + per_page - 1) // per_page,
        }


class ResponseUtils:
    """Common response formatting utilities."""

    @staticmethod
    def success(
        data: Any = None, message: str = None, request_id: str = None
    ) -> Dict[str, Any]:
        """Create standardized success response."""
        return create_success_response(
            data=data, message=message, request_id=request_id
        )

    @staticmethod
    def error(
        error_type: str, error_code: str, message: str, request_id: str = None
    ) -> Dict[str, Any]:
        """Create standardized error response."""
        return create_error_response(
            error_type=error_type,
            error_code=error_code,
            message=message,
            request_id=request_id,
        )

    @staticmethod
    def paginated(
        items: List[Any], page: int, per_page: int, total: int, request_id: str = None
    ) -> Dict[str, Any]:
        """Create standardized paginated response."""
        return create_paginated_response(
            data=items, page=page, per_page=per_page, total=total, request_id=request_id
        )


class CacheUtils:
    """Common caching utilities."""

    @staticmethod
    def generate_cache_key(*parts: str) -> str:
        """Generate consistent cache key from parts."""
        return ":".join(str(part) for part in parts if part)

    @staticmethod
    def get_user_cache_key(user_id: str, cache_type: str) -> str:
        """Generate user-specific cache key."""
        return CacheUtils.generate_cache_key("user", user_id, cache_type)

    @staticmethod
    def get_service_cache_key(service: str, cache_type: str) -> str:
        """Generate service-specific cache key."""
        return CacheUtils.generate_cache_key("service", service, cache_type)


class DateTimeUtils:
    """Common datetime utilities."""

    @staticmethod
    def utc_now() -> datetime:
        """Get current UTC datetime."""
        return datetime.now(timezone.utc)

    @staticmethod
    def format_datetime(dt: datetime) -> str:
        """Format datetime for API responses."""
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.isoformat()

    @staticmethod
    def parse_datetime(dt_str: str) -> datetime:
        """Parse datetime string."""
        try:
            return datetime.fromisoformat(dt_str.replace("Z", "+00:00"))
        except ValueError:
            raise ValidationError("Invalid datetime format")


class SecurityUtils:
    """Common security utilities."""

    @staticmethod
    def sanitize_string(value: str, max_length: int = 255) -> str:
        """Sanitize string input."""
        if not isinstance(value, str):
            raise ValidationError("Value must be a string")

        # Remove null bytes and control characters
        sanitized = re.sub(r"[\x00-\x1f\x7f-\x9f]", "", value)

        # Trim whitespace
        sanitized = sanitized.strip()

        # Enforce length limit
        if len(sanitized) > max_length:
            sanitized = sanitized[:max_length]

        return sanitized

    @staticmethod
    def validate_service_name(service: str) -> str:
        """Validate and sanitize service name."""
        if not service:
            raise ValidationError("Service name is required")

        service = SecurityUtils.sanitize_string(service, 50).lower()

        # Allow only alphanumeric, underscore, hyphen
        if not re.match(r"^[a-zA-Z0-9_-]+$", service):
            raise ValidationError("Service name contains invalid characters")

        return service


class LoggingUtils:
    """Common logging utilities."""

    @staticmethod
    def log_user_action(user_id: str, action: str, details: Dict[str, Any] = None):
        """Log user action with consistent format."""
        logger.info(
            f"User action: {action}",
            extra={
                "user_id": user_id,
                "action": action,
                "details": details or {},
                "timestamp": DateTimeUtils.utc_now().isoformat(),
            },
        )

    @staticmethod
    def log_api_call(
        endpoint: str,
        user_id: str = None,
        duration_ms: float = None,
        status: str = "success",
    ):
        """Log API call with performance metrics."""
        logger.info(
            f"API call: {endpoint}",
            extra={
                "endpoint": endpoint,
                "user_id": user_id,
                "duration_ms": duration_ms,
                "status": status,
                "timestamp": DateTimeUtils.utc_now().isoformat(),
            },
        )


# Decorator for common error handling
def handle_common_errors(func):
    """Decorator to handle common exceptions and return standardized responses."""

    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except ValidationError as e:
            return ResponseUtils.error("ValidationError", "VALIDATION_ERROR", e.message)
        except AuthorizationError as e:
            return ResponseUtils.error(
                "AuthorizationError", "AUTHORIZATION_ERROR", e.message
            )
        except Exception as e:
            logger.error(f"Unexpected error in {func.__name__}: {e}", exc_info=True)
            return ResponseUtils.error(
                "InternalError", "INTERNAL_ERROR", "An unexpected error occurred"
            )

    return wrapper


# Common query filters
class QueryFilters:
    """Common database query filters."""

    @staticmethod
    def by_date_range(
        query, date_field, start_date: datetime = None, end_date: datetime = None
    ):
        """Filter query by date range."""
        if start_date:
            query = query.filter(date_field >= start_date)
        if end_date:
            query = query.filter(date_field <= end_date)
        return query

    @staticmethod
    def by_status(query, status_field, status: str):
        """Filter query by status."""
        if status:
            query = query.filter(status_field == status)
        return query

    @staticmethod
    def by_user(query, user_field, user_id: str):
        """Filter query by user ID."""
        if user_id:
            ValidationUtils.validate_uuid(user_id, "User ID")
            query = query.filter(user_field == user_id)
        return query
