"""Custom validation utilities for Pydantic schemas."""


import re
from datetime import datetime
from typing import Any, Dict, List, Optional
from app.core.pydantic_compat import field_validator
import json


def validate_phone_number(phone: str) -> str:
    """Validate phone number format."""
    # Remove all non - digit characters except +
    cleaned = re.sub(r"[^\d+]", "", phone)

    # Check if it starts with + and has 10 - 15 digits
    if not re.match(r"^\+\d{10,15}$", cleaned):
        raise ValueError("Invalid phone number format. Use international format: +1234567890")

    return cleaned


def validate_service_name(service: str) -> str:
    """Validate service name."""
    if not service or len(service.strip()) == 0:
        raise ValueError("Service name cannot be empty")

    # Convert to lowercase and remove extra spaces
    cleaned = service.lower().strip()

    # Check for valid characters (alphanumeric, underscore, hyphen)
    if not re.match(r"^[a - z0-9_-]+$", cleaned):
        raise ValueError("Service name can only contain letters, numbers, underscores, and hyphens")

    return cleaned


def validate_currency_amount(
        amount: float,
        min_amount: float = 0.01,
        max_amount: float = 100000.0) -> float:
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
    if not re.match(r"^[A - Z0-9]{6}$", cleaned):
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
        r"(?:(?:[A - Z0-9](?:[A - Z0-9-]{0,61}[A - Z0-9])?\.)+[A - Z]{2,6}\.?|"  # domain...
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
        raise ValueError("Maximum duration == 1 year (8760 hours)")

    # Round to 2 decimal places
    return round(hours, 2)


def validate_area_code(code: str) -> str:
    """Validate area code format."""
    if not code:
        return code

    # Remove non - digits
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
        raise ValueError(f'Unsupported carrier. Supported: {", ".join(supported_carriers)}')

    return cleaned


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
        items: List[Any], total: int, page: int, size: int) -> Dict[str, Any]:
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

    # ============================================================================
    # ENHANCED VALIDATORS WITH COMPREHENSIVE ERROR HANDLING
    # ============================================================================


def validate_email(email: str) -> str:
    """Validate email format with comprehensive checks."""
    if not email:
        raise ValueError("Email cannot be empty")

    email = email.strip().lower()

    if len(email) > 254:
        raise ValueError("Email is too long (max 254 characters)")

    # RFC 5322 simplified email validation
    email_pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    if not re.match(email_pattern, email):
        raise ValueError("Invalid email format")

    # Check for consecutive dots
    if ".." in email:
        raise ValueError("Email cannot contain consecutive dots")

    # Check if starts or ends with dot
    if email.startswith(".") or email.endswith("."):
        raise ValueError("Email cannot start or end with a dot")

    return email


def validate_password_strength(password: str) -> str:
    """Validate password strength with detailed requirements."""
    if not password:
        raise ValueError("Password cannot be empty")

    if len(password) < 8:
        raise ValueError("Password must be at least 8 characters long")

    if len(password) > 128:
        raise ValueError("Password is too long (max 128 characters)")

    # Check for at least one uppercase letter
    if not re.search(r"[A-Z]", password):
        raise ValueError("Password must contain at least one uppercase letter")

    # Check for at least one lowercase letter
    if not re.search(r"[a-z]", password):
        raise ValueError("Password must contain at least one lowercase letter")

    # Check for at least one digit
    if not re.search(r"\d", password):
        raise ValueError("Password must contain at least one digit")

    # Check for at least one special character
    if not re.search(r'[!@#$%^&*()_+\-=\[\]{};:\'",.<>?/\\|`~]', password):
        raise ValueError("Password must contain at least one special character")

    return password


def validate_country_code(code: str) -> str:
    """Validate country code format."""
    if not code:
        raise ValueError("Country code cannot be empty")

    code = code.strip().upper()

    # Accept 2-letter ISO codes or country names
    if len(code) == 2:
        if not re.match(r"^[A-Z]{2}$", code):
            raise ValueError("Invalid country code format")
    else:
        # Accept country names (lowercase)
        code = code.lower()
        if not re.match(r"^[a-z]{2,}$", code):
            raise ValueError("Invalid country format")

    return code


def validate_positive_number(value: float, field_name: str = "value") -> float:
    """Validate that a number is positive."""
    if value is None:
        raise ValueError(f"{field_name} cannot be None")

    if not isinstance(value, (int, float)):
        raise ValueError(f"{field_name} must be a number")

    if value <= 0:
        raise ValueError(f"{field_name} must be positive")

    return float(value)


def validate_non_negative_number(value: float, field_name: str = "value") -> float:
    """Validate that a number is non-negative."""
    if value is None:
        raise ValueError(f"{field_name} cannot be None")

    if not isinstance(value, (int, float)):
        raise ValueError(f"{field_name} must be a number")

    if value < 0:
        raise ValueError(f"{field_name} cannot be negative")

    return float(value)


def validate_string_length(
        value: str,
        min_length: int = 1,
        max_length: int = 255,
        field_name: str = "value") -> str:
    """Validate string length with bounds."""
    if not value:
        raise ValueError(f"{field_name} cannot be empty")

    value = value.strip()

    if len(value) < min_length:
        raise ValueError(f"{field_name} must be at least {min_length} characters")

    if len(value) > max_length:
        raise ValueError(f"{field_name} cannot exceed {max_length} characters")

    return value


def validate_enum_value(value: str, allowed_values: List[str], field_name: str = "value") -> str:
    """Validate that value is in allowed list."""
    if not value:
        raise ValueError(f"{field_name} cannot be empty")

    value = value.lower().strip()

    if value not in [v.lower() for v in allowed_values]:
        raise ValueError(f"{field_name} must be one of: {', '.join(allowed_values)}")

    return value


def validate_date_format(date_str: str, format_str: str = "%Y-%m-%d") -> datetime:
    """Validate date format."""
    if not date_str:
        raise ValueError("Date cannot be empty")

    try:
        return datetime.strptime(date_str.strip(), format_str)
    except ValueError:
        raise ValueError(f"Invalid date format. Expected {format_str}")


def validate_url(url: str) -> str:
    """Validate URL format."""
    if not url:
        raise ValueError("URL cannot be empty")

    url = url.strip()

    # Basic URL validation
    url_pattern = re.compile(
        r"^https?://"  # http:// or https://
        r"(?:(?:[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?\.)+[a-zA-Z]{2,6}\.?|"  # domain
        r"localhost|"  # localhost
        r"\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})"  # IP
        r"(?::\d+)?"  # optional port
        r"(?:/?|[/?]\S+)$",
        re.IGNORECASE,
    )

    if not url_pattern.match(url):
        raise ValueError("Invalid URL format")

    if len(url) > 2048:
        raise ValueError("URL is too long (max 2048 characters)")

    return url


def validate_uuid(value: str) -> str:
    """Validate UUID format."""
    if not value:
        raise ValueError("UUID cannot be empty")

    uuid_pattern = r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$"
    if not re.match(uuid_pattern, value.lower()):
        raise ValueError("Invalid UUID format")

    return value


def validate_json_string(value: str) -> dict:
    """Validate and parse JSON string."""
    if not value:
        raise ValueError("JSON string cannot be empty")

    try:
        return json.loads(value)
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON format: {str(e)}")


def validate_ip_address(ip: str) -> str:
    """Validate IP address format (IPv4 or IPv6)."""
    if not ip:
        raise ValueError("IP address cannot be empty")

    ip = ip.strip()

    # IPv4 validation
    ipv4_pattern = r"^(\d{1,3}\.){3}\d{1,3}$"
    if re.match(ipv4_pattern, ip):
        parts = ip.split(".")
    if all(0 <= int(part) <= 255 for part in parts):
        return ip

    # IPv6 validation (simplified)
    ipv6_pattern = r"^([0-9a-fA-F]{0,4}:){2,7}[0-9a-fA-F]{0,4}$"
    if re.match(ipv6_pattern, ip):
        return ip

        raise ValueError("Invalid IP address format")


def validate_credit_amount(amount: float) -> float:
    """Validate credit amount for transactions."""
    if amount is None:
        raise ValueError("Amount cannot be None")

    if not isinstance(amount, (int, float)):
        raise ValueError("Amount must be a number")

    if amount <= 0:
        raise ValueError("Amount must be positive")

    if amount > 1000000:
        raise ValueError("Amount exceeds maximum limit (1,000,000)")

    # Round to 2 decimal places
    return round(amount, 2)


def validate_query_parameters(page: Optional[int] = None, limit: Optional[int] = None) -> tuple:
    """Validate pagination query parameters."""
    # Validate page
    if page is None:
        page = 1
    elif not isinstance(page, int):
        raise ValueError("Page must be an integer")
    elif page < 1:
        raise ValueError("Page must be at least 1")

    # Validate limit
    if limit is None:
        limit = 20
    elif not isinstance(limit, int):
        raise ValueError("Limit must be an integer")
    elif limit < 1:
        raise ValueError("Limit must be at least 1")
    elif limit > 100:
        raise ValueError("Limit cannot exceed 100")

    return page, limit


def validate_search_query(query: str, min_length: int = 1, max_length: int = 255) -> str:
    """Validate search query."""
    if not query:
        raise ValueError("Search query cannot be empty")

    query = query.strip()

    if len(query) < min_length:
        raise ValueError(f"Search query must be at least {min_length} character(s)")

    if len(query) > max_length:
        raise ValueError(f"Search query cannot exceed {max_length} characters")

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
