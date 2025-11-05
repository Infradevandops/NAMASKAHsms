"""Custom validation utilities for Pydantic schemas."""
import re
from typing import Any, Dict, List

from pydantic import validator


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
        return code

    # Remove whitespace
    cleaned = code.strip().upper()

    # Check format: 6 alphanumeric characters
    if not re.match(r"^[A-Z0-9]{6}$", cleaned):
        raise ValueError("Referral code must be 6 alphanumeric characters")

    return cleaned


def validate_api_key_name(name: str) -> str:
    """Validate API key name."""
    if not name or len(name.strip()) == 0:
        raise ValueError("API key name cannot be empty")

    cleaned = name.strip()

    if len(cleaned) > 100:
        raise ValueError("API key name cannot exceed 100 characters")

    return cleaned


def validate_webhook_url(url: str) -> str:
    """Validate webhook URL."""
    if not url or len(url.strip()) == 0:
        raise ValueError("Webhook URL cannot be empty")

    cleaned = url.strip()

    # Basic URL validation
    url_pattern = re.compile(
        r"^https?://"  # http:// or https://
        r"(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|"  # domain...
        r"localhost|"  # localhost...
        r"\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})"  # ...or ip
        r"(?::\d+)?"  # optional port
        r"(?:/?|[/?]\S+)$",
        re.IGNORECASE,
    )

    if not url_pattern.match(cleaned):
        raise ValueError("Invalid webhook URL format")

    return cleaned


def validate_duration_hours(hours: float) -> float:
    """Validate rental duration in hours."""
    if hours <= 0:
        raise ValueError("Duration must be positive")

    if hours > 8760:  # 1 year
        raise ValueError("Maximum duration is 1 year (8760 hours)")

    # Round to 2 decimal places
    return round(hours, 2)


def validate_area_code(code: str) -> str:
    """Validate area code format."""
    if not code:
        return code

    # Remove non-digits
    cleaned = re.sub(r"\D", "", code)

    # Check if it's 3 digits
    if not re.match(r"^\d{3}$", cleaned):
        raise ValueError("Area code must be 3 digits")

    return cleaned


def validate_carrier_name(carrier: str) -> str:
    """Validate carrier name."""
    if not carrier:
        return carrier

    cleaned = carrier.lower().strip()

    # List of supported carriers
    supported_carriers = [
        "verizon",
        "att",
        "tmobile",
        "sprint",
        "boost",
        "cricket",
        "metropcs",
        "tracfone",
        "straighttalk",
        "uscellular",
    ]

    if cleaned not in supported_carriers:
        raise ValueError(
            f'Unsupported carrier. Supported: {", ".join(supported_carriers)}'
        )

    return cleaned


class ValidationMixin:
    """Mixin class with common validators for Pydantic models."""

    @validator("phone_number", pre=True, allow_reuse=True)
    def validate_phone(cls, v):
        if v:
            return validate_phone_number(v)
        return v

    @validator("service_name", pre=True, allow_reuse=True)
    def validate_service(cls, v):
        if v:
            return validate_service_name(v)
        return v

    @validator("referral_code", pre=True, allow_reuse=True)
    def validate_referral(cls, v):
        if v:
            return validate_referral_code(v)
        return v

    @validator("area_code", pre=True, allow_reuse=True)
    def validate_area(cls, v):
        if v:
            return validate_area_code(v)
        return v

    @validator("carrier", pre=True, allow_reuse=True)
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

    return cleaned.strip()


def validate_pagination_params(page: int, size: int) -> tuple:
    """Validate pagination parameters."""
    page = max(page, 1)

    if size < 1:
        size = 10
    elif size > 100:
        size = 100

    return page, size


def create_pagination_response(
    items: List[Any], total: int, page: int, size: int
) -> Dict[str, Any]:
    """Create standardized pagination response."""
    pages = (total + size - 1) // size  # Ceiling division

    return {
        "items": items,
        "total": total,
        "page": page,
        "size": size,
        "pages": pages,
        "has_next": page < pages,
        "has_prev": page > 1,
    }
