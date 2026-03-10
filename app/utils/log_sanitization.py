"""Log sanitization utilities to prevent log injection attacks."""

import re
from typing import Any, Dict, Union


def sanitize_log_input(data: Union[str, Dict, Any]) -> str:
    """Sanitize input for safe logging to prevent log injection."""
    if data is None:
        return "None"

    if not isinstance(data, str):
        data = str(data)

    sanitized = re.sub(r"[\r\n\t\x00-\x1f\x7f-\x9f]", "_", data)
    sanitized = re.sub(r"\x1b\[[0-9;]*m", "", sanitized)

    max_length = 500
    if len(sanitized) > max_length:
        sanitized = sanitized[:max_length] + "...[truncated]"

    return sanitized


def sanitize_user_id(user_id: str) -> str:
    """Sanitize user ID for logging."""
    if not user_id:
        return "unknown"

    sanitized = re.sub(r"[^a-zA-Z0-9_-]", "_", str(user_id))

    if len(sanitized) > 50:
        sanitized = sanitized[:50] + "..."

    return sanitized


def sanitize_service_name(service_name: str) -> str:
    """Sanitize service name for logging."""
    if not service_name:
        return "unknown"

    sanitized = re.sub(r"[^a-zA-Z0-9_.-]", "_", str(service_name))

    if len(sanitized) > 100:
        sanitized = sanitized[:100] + "..."

    return sanitized


def create_safe_log_context(**kwargs) -> Dict[str, str]:
    """Create a safe logging context dictionary."""
    safe_context = {}

    for key, value in kwargs.items():
        safe_key = re.sub(r"[^a-zA-Z0-9_]", "_", str(key))

        if key in ["user_id", "user"]:
            safe_value = sanitize_user_id(value)
        elif key in ["service", "service_name"]:
            safe_value = sanitize_service_name(value)
        else:
            safe_value = sanitize_log_input(value)

        safe_context[safe_key] = safe_value

    return safe_context


def safe_log_format(message: str, **kwargs) -> str:
    """Format a log message safely with context."""
    safe_message = sanitize_log_input(message)

    if kwargs:
        safe_context = create_safe_log_context(**kwargs)
        context_str = " ".join([f"{k}={v}" for k, v in safe_context.items()])
        return f"{safe_message} [{context_str}]"

    return safe_message
