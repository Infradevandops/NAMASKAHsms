"""SQL injection prevention utilities."""


import re
from typing import Any, List
from sqlalchemy import text
from sqlalchemy.orm import Session


def validate_identifier(identifier: str, max_length: int = 128) -> str:
    """Validate SQL identifier (table/column name)."""
    if not identifier or len(identifier) > max_length:
        raise ValueError(f"Invalid identifier: {identifier}")

    if not re.match(r"^[a-zA-Z_][a-zA-Z0-9_]*$", identifier):
        raise ValueError(f"Invalid identifier format: {identifier}")

    return identifier


def validate_sort_field(field: str, allowed_fields: List[str]) -> str:
    """Validate sort field is in allowed list."""
    if field not in allowed_fields:
        raise ValueError(f"Invalid sort field: {field}")
    return field


def validate_sort_order(order: str) -> str:
    """Validate sort order is ASC or DESC."""
    order = order.upper()
    if order not in ["ASC", "DESC"]:
        raise ValueError(f"Invalid sort order: {order}")
    return order


def safe_raw_query(db: Session, query_str: str, params: dict = None) -> Any:
    """Execute raw SQL query safely with parameterized queries."""
    if params is None:
        params = {}

    if "%" in query_str or "$" in query_str:
        raise ValueError("Use :param syntax for parameterized queries, not % or $")

    try:
        result = db.execute(text(query_str), params)
        return result
    except Exception as e:
        raise ValueError(f"Query execution failed: {str(e)}")


def audit_query_safety(query_str: str) -> bool:
    """Audit query for potential SQL injection patterns."""
    dangerous_patterns = [
        r"'\s*\+\s*",
        r"'\s*or\s*'",
        r"'\s*;\s*",
        r"--\s*",
        r"/\*.*\*/",
        r"xp_",
        r"sp_",
    ]

    query_lower = query_str.lower()
    for pattern in dangerous_patterns:
        if re.search(pattern, query_lower):
            return False

    return True


class SQLSafetyValidator:
    """Validator for SQL safety in queries."""

    @staticmethod
    def validate_string_input(value: str, max_length: int = 1000) -> str:
        """Validate and sanitize string input."""
        if not isinstance(value, str):
            raise ValueError("Input must be string")

        if len(value) > max_length:
            raise ValueError(f"Input exceeds maximum length of {max_length}")

        value = value.replace("\x00", "")
        return value

    @staticmethod
    def validate_numeric_input(value: Any, min_val: int = None, max_val: int = None) -> int:
        """Validate numeric input."""
        try:
            num = int(value)
        except (ValueError, TypeError):
            raise ValueError("Input must be numeric")

        if min_val is not None and num < min_val:
            raise ValueError(f"Value must be >= {min_val}")

        if max_val is not None and num > max_val:
            raise ValueError(f"Value must be <= {max_val}")

        return num

    @staticmethod
    def validate_email(email: str) -> str:
        """Validate email format."""
        if not re.match(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$", email):
            raise ValueError("Invalid email format")
        return email.lower()
