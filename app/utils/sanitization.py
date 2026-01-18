"""Input sanitization utilities to prevent XSS attacks."""

import html
import re
import os
from typing import Any, Dict, List, Union


def sanitize_html(text: str) -> str:
    """Sanitize HTML content to prevent XSS attacks."""
    if not isinstance(text, str):
        return str(text)

    # HTML escape the content
    sanitized = html.escape(text)

    # Remove any remaining script tags or javascript
    sanitized = re.sub(r"<script[^>]*>.*?</script>", "", sanitized, flags=re.IGNORECASE | re.DOTALL)
    sanitized = re.sub(r"javascript:", "", sanitized, flags=re.IGNORECASE)
    sanitized = re.sub(r"on\w+\s*=", "", sanitized, flags=re.IGNORECASE)

    return sanitized


def sanitize_user_input(data: Union[str, Dict, List, Any]) -> Union[str, Dict, List, Any]:
    """Recursively sanitize user input data."""
    if isinstance(data, str):
        return sanitize_html(data)
    elif isinstance(data, dict):
        return {key: sanitize_user_input(value) for key, value in data.items()}
    elif isinstance(data, list):
        return [sanitize_user_input(item) for item in data]
    else:
        return data


def sanitize_email_content(content: str) -> str:
    """Sanitize email content while preserving basic HTML formatting."""
    if not isinstance(content, str):
        return str(content)

    # Allow basic HTML tags but escape everything else
    allowed_tags = ["p", "br", "strong", "b", "em", "i", "h1", "h2", "h3", "h4", "h5", "h6"]

    # First escape all HTML
    sanitized = html.escape(content)

    # Then unescape allowed tags
    for tag in allowed_tags:
        sanitized = sanitized.replace(f"&lt;{tag}&gt;", f"<{tag}>")
        sanitized = sanitized.replace(f"&lt;/{tag}&gt;", f"</{tag}>")

    return sanitized


def validate_and_sanitize_response(response_data: Dict) -> Dict:
    """Validate and sanitize API response data."""
    if not isinstance(response_data, dict):
        return response_data

    sanitized = {}
    for key, value in response_data.items():
        if key in ["message", "description", "name", "email", "title", "content"]:
            # Sanitize user - facing text fields
            sanitized[key] = sanitize_html(str(value)) if value is not None else value
        elif isinstance(value, (dict, list)):
            # Recursively sanitize nested data
            sanitized[key] = sanitize_user_input(value)
        else:
            sanitized[key] = value

    return sanitized


def sanitize_filename(filename: str) -> str:
    """Sanitize filename to prevent directory traversal and invalid characters."""
    if not isinstance(filename, str):
        return "unnamed_file"

    # Remove directory separators
    filename = os.path.basename(filename)
    
    # Remove invalid characters (keep alphanumeric, dots, dashes, underscores)
    filename = re.sub(r'[^a-zA-Z0-9._-]', '', filename)
    
    # Limit length
    if len(filename) > 255:
        base, ext = os.path.splitext(filename)
        filename = base[:255-len(ext)] + ext
        
    # Prevent empty filename
    if not filename:
        filename = "unnamed_file"
        
    return filename

