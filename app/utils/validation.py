"""Validation utilities for input validation and data sanitization."""
import re
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse

import phonenumbers
from phonenumbers import NumberParseException


def validate_email(email: str) -> bool:
    """Validate email format."""
    pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    return bool(re.match(pattern, email))


def validate_phone_number(phone: str, region: Optional[str] = None) -> Dict[str, Any]:
    """Validate phone number format and return details."""
    try:
        parsed = phonenumbers.parse(phone, region)
        is_valid = phonenumbers.is_valid_number(parsed)

        return {
            "is_valid": is_valid,
            "formatted": phonenumbers.format_number(
                parsed, phonenumbers.PhoneNumberFormat.E164
            )
            if is_valid
            else None,
            "country_code": parsed.country_code if is_valid else None,
            "national_number": parsed.national_number if is_valid else None,
        }
    except NumberParseException:
        return {
            "is_valid": False,
            "formatted": None,
            "country_code": None,
            "national_number": None,
        }


def validate_url(url: str) -> bool:
    """Validate URL format."""
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except (ValueError, TypeError, AttributeError):
        return False


def validate_service_name(service: str) -> bool:
    """Validate service name against supported services."""
    supported_services = {
        "telegram",
        "whatsapp",
        "discord",
        "instagram",
        "twitter",
        "facebook",
        "google",
        "microsoft",
        "github",
        "linkedin",
    }
    return service.lower() in supported_services


def validate_currency_amount(
    amount: float, min_amount: float = 0.01, max_amount: float = 100000.0
) -> Dict[str, Any]:
    """Validate currency amount."""
    is_valid = min_amount <= amount <= max_amount

    return {
        "is_valid": is_valid,
        "amount": round(amount, 2),
        "min_amount": min_amount,
        "max_amount": max_amount,
    }


def sanitize_input(text: str, max_length: int = 1000) -> str:
    """Sanitize text input by removing dangerous characters."""
    if not text:
        return ""

    # Remove HTML tags
    text = re.sub(r"<[^>]+>", "", text)

    # Remove script tags and content
    text = re.sub(r"<script.*?</script>", "", text, flags=re.DOTALL | re.IGNORECASE)

    # Limit length
    text = text[:max_length]

    # Clean whitespace
    text = re.sub(r"\s+", " ", text).strip()

    return text


def validate_api_key_name(name: str) -> bool:
    """Validate API key name format."""
    if not name or len(name) < 3 or len(name) > 50:
        return False

    # Only alphanumeric, spaces, hyphens, underscores
    pattern = r"^[a-zA-Z0-9\s\-_]+$"
    return bool(re.match(pattern, name))


def validate_pagination_params(
    page: int, size: int, max_size: int = 100
) -> Dict[str, Any]:
    """Validate pagination parameters."""
    page = max(1, page)
    size = max(1, min(size, max_size))

    return {"page": page, "size": size, "offset": (page - 1) * size}


def validate_date_range(date_from: str, date_to: str) -> Dict[str, Any]:
    """Validate date range format (ISO format)."""
    from datetime import datetime

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


def validate_webhook_url(url: str) -> Dict[str, Any]:
    """Validate webhook URL with additional security checks."""
    if not validate_url(url):
        return {"is_valid": False, "reason": "Invalid URL format"}

    parsed = urlparse(url)

    # Must be HTTPS
    if parsed.scheme != "https":
        return {"is_valid": False, "reason": "Must use HTTPS"}

    # No localhost or private IPs
    hostname = parsed.hostname
    if (
        hostname in ["localhost", "127.0.0.1", "0.0.0.0"]
        or hostname.startswith("192.168.")
        or hostname.startswith("10.")
    ):
        return {"is_valid": False, "reason": "Private/local addresses not allowed"}

    return {"is_valid": True, "reason": None}


class ValidationMixin:
    """Mixin class for common validation methods."""

    @staticmethod
    def validate_required_fields(
        data: Dict[str, Any], required_fields: List[str]
    ) -> List[str]:
        """Validate that required fields are present and not empty."""
        missing_fields = []

        for field in required_fields:
            if field not in data or not data[field]:
                missing_fields.append(field)

        return missing_fields

    @staticmethod
    def validate_field_lengths(
        data: Dict[str, Any], field_limits: Dict[str, int]
    ) -> List[str]:
        """Validate field length limits."""
        invalid_fields = []

        for field, max_length in field_limits.items():
            if (
                field in data
                and isinstance(data[field], str)
                and len(data[field]) > max_length
            ):
                invalid_fields.append(f"{field} exceeds {max_length} characters")

        return invalid_fields
