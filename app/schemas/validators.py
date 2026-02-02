"""Custom validation utilities for Pydantic schemas."""

import re
from datetime import datetime
from typing import Any, Dict, List, Optional
from app.core.pydantic_compat import field_validator
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

    # Round to 2 decimal places
    return round(amount, 2)


def validate_referral_code(code: str) -> str:
    """Validate referral code format."""
    if not code:
        raise ValueError("Referral code cannot be empty")

    code = code.strip().upper()

    if len(code) != 6 or not code.isalnum():
        raise ValueError("Referral code must be 6 alphanumeric characters")

    return code


def validate_api_key_name(name: str) -> str:
    """Validate API key name."""
    if not name or not name.strip():
        raise ValueError("API key name cannot be empty")

    cleaned = name.strip()

    if len(cleaned) < 3:
        raise ValueError("API key name must be at least 3 characters")

    if len(cleaned) > 50:
        raise ValueError("API key name cannot exceed 50 characters")

    if not re.match(r"^[a-zA-Z0-9\s_-]+$", cleaned):
        raise ValueError(
            "API key name can only contain letters, numbers, spaces, underscores, and hyphens"
        )

    return cleaned


def validate_webhook_url(url: str) -> str:
    """Validate webhook URL format."""
    if not url:
        raise ValueError("Webhook URL cannot be empty")

    url = url.strip()

    if not re.match(r"^https?://", url):
        raise ValueError("Webhook URL must start with http:// or https://")

    if len(url) > 500:
        raise ValueError("Webhook URL cannot exceed 500 characters")

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
        raise ValueError("Area code cannot be empty")

    cleaned = area_code.strip()

    if not re.match(r"^\d{3}$", cleaned):
        raise ValueError("Area code must be exactly 3 digits")

    return cleaned


def validate_carrier_name(carrier: str) -> str:
    """Validate carrier name."""
    if not carrier:
        raise ValueError("Carrier name cannot be empty")

    cleaned = carrier.strip().lower()

    if len(cleaned) < 2:
        raise ValueError("Carrier name must be at least 2 characters")

    if not re.match(r"^[a-z0-9\s_-]+$", cleaned):
        raise ValueError(
            "Carrier name can only contain letters, numbers, spaces, underscores, and hyphens"
        )

    return cleaned


def validate_email(email: str) -> str:
    """Validate email format."""
    if not email:
        raise ValueError("Email cannot be empty")

    email = email.strip().lower()

    if not re.match(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$", email):
        raise ValueError("Invalid email format")

    return email


def validate_password_strength(password: str) -> str:
    """Validate password strength."""
    if not password:
        raise ValueError("Password cannot be empty")

    if len(password) < 8:
        raise ValueError("Password must be at least 8 characters long")

    if not re.search(r"[A-Z]", password):
        raise ValueError("Password must contain at least one uppercase letter")

    if not re.search(r"[a-z]", password):
        raise ValueError("Password must contain at least one lowercase letter")

    if not re.search(r"\d", password):
        raise ValueError("Password must contain at least one digit")

    if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
        raise ValueError("Password must contain at least one special character")

    return password


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


    def sanitize_input(text: str) -> str:
        """Sanitize text input for security."""
        if not text:
        return ""

    # Remove dangerous patterns
        dangerous_patterns = [
        r"<script[^>]*>.*?</script>",
        r"javascript:",
        r"on\w+\s*=",
        r"<iframe[^>]*>.*?</iframe>",
        r"<object[^>]*>.*?</object>",
        r"<embed[^>]*>.*?</embed>",
        ]

        cleaned = text

        for pattern in dangerous_patterns:
        cleaned = re.sub(pattern, "", cleaned, flags=re.IGNORECASE | re.DOTALL)

    # Remove potentially dangerous characters
        dangerous_chars = ["<", ">", '"', "'", "&", ";", "|", "`"]
        for char in dangerous_chars:
        if char in cleaned:
            cleaned = cleaned.replace(char, "")

        return cleaned.strip()


    def validate_pagination_params(page: int, per_page: int) -> tuple[int, int]:
        """Validate pagination parameters."""
        if page < 1:
        page = 1

        if per_page < 1:
        per_page = 10
        elif per_page > 100:
        per_page = 100

        return page, per_page


    def create_pagination_response(
        items: List[Any], page: int, per_page: int, total: int
        ) -> Dict[str, Any]:
        """Create standardized pagination response."""
        total_pages = (total + per_page - 1) // per_page

        return {
        "items": items,
        "pagination": {
            "page": page,
            "per_page": per_page,
            "total": total,
            "total_pages": total_pages,
            "has_next": page < total_pages,
            "has_prev": page > 1,
        },
        }


    def validate_search_query(query: str) -> str:
        """Validate search query for security."""
        if not query:
        raise ValueError("Search query cannot be empty")

        query = query.strip()

        if len(query) < 2:
        raise ValueError("Search query must be at least 2 characters")

        if len(query) > 100:
        raise ValueError("Search query cannot exceed 100 characters")

    # Remove potentially dangerous characters
        dangerous_chars = ["<", ">", '"', "'", "&", ";", "|", "`"]
        for char in dangerous_chars:
        if char in query:
            raise ValueError(f"Search query contains invalid character: {char}")

        return query


    def validate_date_range(date_from: str, date_to: str) -> Dict[str, Any]:
        """Validate date range format (ISO format)."""
        try:
        start_date = datetime.fromisoformat(date_from.replace("Z", "+00:00"))
        end_date = datetime.fromisoformat(date_to.replace("Z", "+00:00"))

        is_valid = start_date <= end_date

        return {
            "is_valid": is_valid,
            "start_date": start_date,
            "end_date": end_date,
            "days_diff": (end_date - start_date).days,
        }
        except ValueError:
        return {"is_valid": False, "start_date": None, "end_date": None, "days_diff": 0}