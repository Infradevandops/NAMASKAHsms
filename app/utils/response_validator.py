"""Response validation utilities for API endpoints."""


import logging
from typing import Any, Dict, Optional, Tuple, Type, TypeVar
from pydantic import BaseModel, ValidationError

logger = logging.getLogger(__name__)

T = TypeVar("T", bound=BaseModel)


class ResponseValidationError(Exception):

    """Exception raised when response validation fails."""

    def __init__(self, message: str, errors: list = None):

        self.message = message
        self.errors = errors or []
        super().__init__(self.message)


    def validate_response(data: Any, schema: Type[T]) -> T:

        """Validate response data against a Pydantic schema.

        Args:
        data: The response data to validate
        schema: The Pydantic schema class to validate against

        Returns:
        The validated data as an instance of the schema

        Raises:
        ResponseValidationError: If validation fails
        """
        try:
        return schema.parse_obj(data)
        except ValidationError as e:
        error_messages = []
        for error in e.errors():
            field = ".".join(str(loc) for loc in error["loc"])
            message = error["msg"]
            error_messages.append(f"{field}: {message}")

        logger.error(f"Response validation failed: {error_messages}")
        raise ResponseValidationError(
            f"Response validation failed: {'; '.join(error_messages)}",
            errors=e.errors(),
        )


    def validate_response_safe(data: Any, schema: Type[T]) -> Tuple[bool, Optional[T], Optional[str]]:

        """Safely validate response data without raising exceptions.

        Args:
        data: The response data to validate
        schema: The Pydantic schema class to validate against

        Returns:
        Tuple of (is_valid, validated_data, error_message)
        """
        try:
        validated = validate_response(data, schema)
        return True, validated, None
        except ResponseValidationError as e:
        return False, None, e.message


    def check_required_fields(data: Dict[str, Any], required_fields: list[str]) -> Tuple[bool, list[str]]:

        """Check if all required fields are present in the response data.

        Args:
        data: The response data dictionary
        required_fields: List of required field names

        Returns:
        Tuple of (all_present, missing_fields)
        """
        missing_fields = [field for field in required_fields if field not in data]
        return len(missing_fields) == 0, missing_fields