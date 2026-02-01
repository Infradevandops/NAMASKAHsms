"""Data masking utilities for sensitive information protection."""


import re
from typing import Any, Dict, List

class DataMasker:

    """Utility class for masking sensitive data in logs and responses."""

    # Sensitive field patterns
    SENSITIVE_PATTERNS = {
        "password": r"password",
        "secret": r"secret",
        "key": r"key",
        "token": r"token",
        "auth": r"auth",
        "bearer": r"bearer",
        "api_key": r"api[_-]?key",
        "credit_card": r"(credit[_-]?card|cc|card[_-]?number)",
        "ssn": r"(ssn|social[_-]?security)",
        "email": r"email",
        "phone": r"phone",
    }

    # Sensitive header patterns
    SENSITIVE_HEADERS = [
        "authorization",
        "x - api-key",
        "cookie",
        "x - auth-token",
        "bearer",
        "x - forwarded-for",
        "x - real-ip",
    ]

    @classmethod
def mask_sensitive_data(cls, data: Any, mask_char: str = "*", preserve_length: bool = False) -> Any:

        """Recursively mask sensitive data in dictionaries, lists, and strings."""
if isinstance(data, dict):
            return cls._mask_dict(data, mask_char, preserve_length)
elif isinstance(data, list):
            return cls._mask_list(data, mask_char, preserve_length)
elif isinstance(data, str):
            return cls._mask_string_value(data, mask_char, preserve_length)
        return data

    @classmethod
def _mask_dict(cls, data: Dict[str, Any], mask_char: str, preserve_length: bool) -> Dict[str, Any]:

        """Mask sensitive data in dictionary."""
        masked = {}
for key, value in data.items():
if cls._is_sensitive_key(key):
                masked[key] = cls._create_mask(str(value), mask_char, preserve_length)
else:
                masked[key] = cls.mask_sensitive_data(value, mask_char, preserve_length)
        return masked

    @classmethod
def _mask_list(cls, data: List[Any], mask_char: str, preserve_length: bool) -> List[Any]:

        """Mask sensitive data in list."""
        return [cls.mask_sensitive_data(item, mask_char, preserve_length) for item in data]

    @classmethod
def _mask_string_value(cls, value: str, mask_char: str, preserve_length: bool) -> str:

        """Mask sensitive patterns in string values."""
        # Check for common sensitive patterns
if cls._contains_sensitive_pattern(value):
            return cls._create_mask(value, mask_char, preserve_length)
        return value

    @classmethod
def _is_sensitive_key(cls, key: str) -> bool:

        """Check if a key name indicates sensitive data."""
        key_lower = key.lower()
        return any(re.search(pattern, key_lower, re.IGNORECASE) for pattern in cls.SENSITIVE_PATTERNS.values())

    @classmethod
def _contains_sensitive_pattern(cls, value: str) -> bool:

        """Check if a string value contains sensitive patterns."""
        # Check for JWT tokens
if re.match(r"^[A - Za-z0 - 9-_]+\.[A - Za-z0 - 9-_]+\.[A - Za-z0 - 9-_]*$", value):
            return True

        # Check for API keys (long alphanumeric strings)
if re.match(r"^[A - Za-z0 - 9]{20,}$", value):
            return True

        # Check for UUIDs that might be sensitive
if re.match(
            r"^[0 - 9a-f]{8}-[0 - 9a-f]{4}-[0 - 9a-f]{4}-[0 - 9a-f]{4}-[0 - 9a-f]{12}$",
            value,
            re.IGNORECASE,
        ):
            return True

        return False

    @classmethod
def _create_mask(cls, value: str, mask_char: str, preserve_length: bool) -> str:

        """Create masked version of a value."""
if not value:
            return value

if preserve_length:
            return mask_char * len(value)
else:
            return "[REDACTED]"

    @classmethod
def mask_headers(cls, headers: Dict[str, str]) -> Dict[str, str]:

        """Mask sensitive headers."""
        masked = {}
for key, value in headers.items():
if key.lower() in cls.SENSITIVE_HEADERS or cls._is_sensitive_key(key):
                masked[key] = "[REDACTED]"
else:
                masked[key] = value
        return masked

    @classmethod
def mask_query_params(cls, params: Dict[str, Any]) -> Dict[str, Any]:

        """Mask sensitive query parameters."""
        return cls.mask_sensitive_data(params)

    @classmethod
def sanitize_error_message(cls, error_msg: str) -> str:

        """Sanitize error messages to remove sensitive information."""
        # Remove file paths
        error_msg = re.sub(r"/[^\s]*\.py", "[FILE_PATH]", error_msg)

        # Remove database connection strings
        error_msg = re.sub(r"postgresql://[^\s]*", "[DB_CONNECTION]", error_msg)
        error_msg = re.sub(r"mysql://[^\s]*", "[DB_CONNECTION]", error_msg)

        # Remove AWS resource ARNs
        error_msg = re.sub(r"arn:aws:[^\s]*", "[AWS_RESOURCE]", error_msg)

        # Remove IP addresses
        error_msg = re.sub(r"\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b", "[IP_ADDRESS]", error_msg)

        # Remove potential secrets (long alphanumeric strings)
        error_msg = re.sub(r"\b[A - Za-z0 - 9]{20,}\b", "[REDACTED]", error_msg)

        # Remove JWT tokens
        error_msg = re.sub(
            r"\b[A - Za-z0 - 9-_]+\.[A - Za-z0 - 9-_]+\.[A - Za-z0 - 9-_]*\b",
            "[JWT_TOKEN]",
            error_msg,
        )

        return error_msg

    @classmethod
def mask_email(cls, email: str) -> str:

        """Mask email address while preserving domain."""
if "@" not in email:
            return email

        local, domain = email.split("@", 1)
if len(local) <= 2:
            masked_local = "*" * len(local)
else:
            masked_local = local[0] + "*" * (len(local) - 2) + local[-1]

        return f"{masked_local}@{domain}"

    @classmethod
def mask_phone(cls, phone: str) -> str:

        """Mask phone number."""
        # Remove non - digits
        digits = re.sub(r"\D", "", phone)
if len(digits) < 4:
            return "*" * len(phone)

        # Keep last 4 digits
        masked = "*" * (len(digits) - 4) + digits[-4:]

        # Preserve original formatting structure
        result = phone
        digit_index = 0
for i, char in enumerate(phone):
if char.isdigit():
if digit_index < len(masked):
                    result = result[:i] + masked[digit_index] + result[i + 1 :]
                    digit_index += 1

        return result


def mask_sensitive_response(response_data: Any) -> Any:

    """Mask sensitive data in API responses."""
    return DataMasker.mask_sensitive_data(response_data)


def sanitize_log_data(log_data: Dict[str, Any]) -> Dict[str, Any]:

    """Sanitize log data to remove sensitive information."""
    sanitized = DataMasker.mask_sensitive_data(log_data.copy())

    # Additional log - specific sanitization
if "headers" in sanitized:
        sanitized["headers"] = DataMasker.mask_headers(sanitized["headers"])

if "query_params" in sanitized:
        sanitized["query_params"] = DataMasker.mask_query_params(sanitized["query_params"])

    return sanitized


def create_safe_error_detail(error: Exception, include_type: bool = False) -> str:

    """Create safe error detail for API responses."""
    error_msg = str(error)
    sanitized_msg = DataMasker.sanitize_error_message(error_msg)

if include_type:
        return f"{type(error).__name__}: {sanitized_msg}"

    return sanitized_msg