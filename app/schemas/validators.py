"""Custom validation utilities for Pydantic schemas."""

import re
from datetime import datetime
from typing import Any, Dict, List, Optional, TypeVar, Generic
from app.core.pydantic_compat import field_validator, BaseModel
import json


def validate_phone_number(phone: str) -> str:
    """Validate phone number format."""
    # Remove all non-digit characters except +
    cleaned = re.sub(r"[^\d+]", "", phone)

    # Check if it starts with + and has 10-15 digits
    if not re.match(r"^\+\d{10,15}$", cleaned):
        raise ValueError(
            "Invalid phone number format. Use international format: +1234567890"
        )

    return cleaned


def validate_service_name(service: str) -> str:
    """Validate service name."""
    if not service or len(service.strip()) == 0:
        raise ValueError("Service name cannot be empty")

    # Convert to lowercase and remove extra spaces
    cleaned = service.lower().strip()

    # Check for valid characters (alphanumeric, underscore, hyphen)
    if not re.match(r"^[a-z0-9_-]+$", cleaned):
        raise ValueError(
            "Service name can only contain letters, numbers, underscores, and hyphens"
        )

    return cleaned


def validate_currency_amount(
    amount: float, min_amount: float = 0.01, max_amount: float = 100000.0
) -> float:
    """Validate currency amount."""
    if amount < min_amount:
        raise ValueError(f"Amount must be at least {min_amount}")

    if amount > max_amount:
        raise ValueError(f"Amount cannot exceed {max_amount}")

    return round(amount, 2)


def validate_email(email: str) -> str:
    """Validate email format."""
    if not email or "@" not in email:
        raise ValueError("Invalid email format")
    
    # Basic email validation
    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if not re.match(email_pattern, email):
        raise ValueError("Invalid email format")
    
    return email.lower().strip()


def validate_password_strength(password: str) -> str:
    """Validate password strength."""
    if len(password) < 8:
        raise ValueError("Password must be at least 8 characters long")
    
    # Check for at least one uppercase, lowercase, digit, and special character
    if not re.search(r'[A-Z]', password):
        raise ValueError("Password must contain at least one uppercase letter")
    
    if not re.search(r'[a-z]', password):
        raise ValueError("Password must contain at least one lowercase letter")
    
    if not re.search(r'\d', password):
        raise ValueError("Password must contain at least one digit")
    
    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        raise ValueError("Password must contain at least one special character")
    
    return password


def validate_referral_code(code: str) -> str:
    """Validate referral code format."""
    if not code:
        return code
    
    code = code.strip().upper()
    if len(code) != 6 or not code.isalnum():
        raise ValueError("Referral code must be 6 alphanumeric characters")
    
    return code


def validate_api_key_name(name: str) -> str:
    """Validate API key name."""
    if not name or not name.strip():
        raise ValueError("API key name cannot be empty")
    
    name = name.strip()
    if len(name) < 3 or len(name) > 50:
        raise ValueError("API key name must be between 3 and 50 characters")
    
    if not re.match(r'^[a-zA-Z0-9_\-\s]+$', name):
        raise ValueError("API key name can only contain letters, numbers, spaces, underscores, and hyphens")
    
    return name


def validate_webhook_url(url: str) -> str:
    """Validate webhook URL format."""
    if not url:
        return url
    
    url = url.strip()
    if not re.match(r'^https?://', url):
        raise ValueError("Webhook URL must start with http:// or https://")
    
    return url


def validate_duration_hours(hours: int) -> int:
    """Validate duration in hours."""
    if hours < 1:
        raise ValueError("Duration must be at least 1 hour")
    
    if hours > 8760:  # 1 year
        raise ValueError("Duration cannot exceed 1 year (8760 hours)")
    
    return hours


def validate_area_code(area_code: str) -> str:
    """Validate area code format."""
    if not area_code:
        return area_code
    
    # Remove non-digits
    cleaned = re.sub(r'\D', '', area_code)
    
    if len(cleaned) != 3:
        raise ValueError("Area code must be 3 digits")
    
    return cleaned


def validate_carrier_name(carrier: str) -> str:
    """Validate carrier name."""
    if not carrier:
        return carrier
    
    carrier = carrier.strip()
    if len(carrier) < 2:
        raise ValueError("Carrier name must be at least 2 characters")
    
    return carrier


def validate_json_field(value: Any) -> Dict[str, Any]:
    """Validate and parse JSON field."""
    if value is None:
        return {}
    
    if isinstance(value, dict):
        return value
    
    if isinstance(value, str):
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            raise ValueError("Invalid JSON format")
    
    raise ValueError("Value must be a dictionary or valid JSON string")


def validate_positive_number(value: float) -> float:
    """Validate that a number is positive."""
    if value < 0:
        raise ValueError("Value must be positive")
    return value


def validate_non_empty_string(value: str) -> str:
    """Validate that a string is not empty."""
    if not value or not value.strip():
        raise ValueError("Value cannot be empty")
    return value.strip()


def sanitize_input(value: str) -> str:
    """Sanitize input string by removing potentially harmful characters."""
    if not value:
        return value
    
    # Remove HTML tags and script content
    value = re.sub(r'<[^>]*>', '', value)
    value = re.sub(r'javascript:', '', value, flags=re.IGNORECASE)
    value = re.sub(r'on\w+\s*=', '', value, flags=re.IGNORECASE)
    
    return value.strip()


def validate_pagination_params(page: int, size: int) -> tuple[int, int]:
    """Validate pagination parameters."""
    if page < 1:
        raise ValueError("Page must be at least 1")
    
    if size < 1:
        raise ValueError("Page size must be at least 1")
    
    if size > 100:
        raise ValueError("Page size cannot exceed 100")
    
    return page, size


T = TypeVar('T')


class PaginationResponse(BaseModel, Generic[T]):
    """Generic pagination response model."""
    
    items: List[T]
    total: int
    page: int
    size: int
    pages: int


    def create_pagination_response(
        items: List[T],
        total: int,
        page: int,
        size: int
        ) -> PaginationResponse[T]:
        """Create a pagination response."""
        pages = (total + size - 1) // size  # Ceiling division
    
        return PaginationResponse(
        items=items,
        total=total,
        page=page,
        size=size,
        pages=pages
        )


class ValidationMixin:
        """Mixin class with common validators for Pydantic models."""

        @field_validator("phone_number", mode="before")
        @classmethod
    def validate_phone(cls, v):
        if v:
        return validate_phone_number(v)
        return v

        @field_validator("service_name", mode="before")
        @classmethod
    def validate_service(cls, v):
        if v:
        return validate_service_name(v)
        return v

        @field_validator("referral_code", mode="before")
        @classmethod
    def validate_referral(cls, v):
        if v:
        return validate_referral_code(v)
        return v

        @field_validator("area_code", mode="before")
        @classmethod
    def validate_area(cls, v):
        if v:
        return validate_area_code(v)
        return v

        @field_validator("carrier", mode="before")
        @classmethod
    def validate_carrier(cls, v):
        if v:
        return validate_carrier_name(v)
        return v
