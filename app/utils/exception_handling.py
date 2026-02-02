"""Exception handling utilities for specific error types."""


import logging
from typing import Any, Dict, Optional
from botocore.exceptions import BotoCoreError, ClientError
from cryptography.fernet import InvalidToken
from sqlalchemy.exc import IntegrityError, OperationalError, SQLAlchemyError
from app.core.exceptions import (
import json

    AuthorizationError,
    ExternalServiceError,
    NamaskahException,
    ValidationError,
)

logger = logging.getLogger(__name__)


class DatabaseError(NamaskahException):

    """Database operation errors."""

    def __init__(

        self,
        message: str = "Database operation failed",
        details: Optional[Dict[str, Any]] = None,
        ):
        super().__init__(message, "DATABASE_ERROR", details)


class EncryptionError(NamaskahException):

        """Encryption/decryption errors."""

    def __init__(

        self,
        message: str = "Encryption operation failed",
        details: Optional[Dict[str, Any]] = None,
        ):
        super().__init__(message, "ENCRYPTION_ERROR", details)


class ConfigurationError(NamaskahException):

        """Configuration errors."""

    def __init__(

        self,
        message: str = "Configuration error",
        details: Optional[Dict[str, Any]] = None,
        ):
        super().__init__(message, "CONFIG_ERROR", details)


class AWSServiceError(ExternalServiceError):

        """AWS service errors."""

    def __init__(

        self,
        service: str,
        message: str = "AWS service error",
        details: Optional[Dict[str, Any]] = None,
        ):
        super().__init__(service, message, details)


    def handle_database_exceptions(func):

        """Decorator to handle database exceptions."""

    def wrapper(*args, **kwargs):

        try:
        return func(*args, **kwargs)
        except IntegrityError as e:
            logger.error(f"Database integrity error in {func.__name__}: {e}")
            raise ValidationError("Data integrity constraint violated", {"original_error": str(e)})
        except OperationalError as e:
            logger.error(f"Database operational error in {func.__name__}: {e}")
            raise DatabaseError(
                "Database connection or \
        operation failed",
                {"original_error": str(e)},
            )
        except SQLAlchemyError as e:
            logger.error(f"SQLAlchemy error in {func.__name__}: {e}")
            raise DatabaseError("Database operation failed", {"original_error": str(e)})

        return wrapper


    def handle_aws_exceptions(service_name: str):

        """Decorator to handle AWS service exceptions."""

    def decorator(func):

    def wrapper(*args, **kwargs):

        try:
        return func(*args, **kwargs)
        except ClientError as e:
                error_code = e.response.get("Error", {}).get("Code", "Unknown")
                error_message = e.response.get("Error", {}).get("Message", str(e))
                logger.error(f"AWS {service_name} client error in {func.__name__}: {error_code} - {error_message}")

        if error_code in ["AccessDenied", "UnauthorizedOperation"]:
                    raise AuthorizationError(
                        f"Access denied to {service_name}",
                        {
                            "service": service_name,
                            "error_code": error_code,
                            "original_error": error_message,
                        },
                    )
        elif error_code in ["ResourceNotFoundException", "NoSuchKey"]:
                    raise ValidationError(
                        f"Resource not found in {service_name}",
                        {
                            "service": service_name,
                            "error_code": error_code,
                            "original_error": error_message,
                        },
                    )
        else:
                    raise AWSServiceError(
                        service_name,
                        f"{service_name} operation failed",
                        {"error_code": error_code, "original_error": error_message},
                    )
        except BotoCoreError as e:
                logger.error(f"AWS {service_name} core error in {func.__name__}: {e}")
                raise AWSServiceError(
                    service_name,
                    f"{service_name} connection failed",
                    {"original_error": str(e)},
                )

        return wrapper

        return decorator


    def handle_encryption_exceptions(func):

        """Decorator to handle encryption exceptions."""

    def wrapper(*args, **kwargs):

        try:
        return func(*args, **kwargs)
        except InvalidToken as e:
            logger.error(f"Invalid encryption token in {func.__name__}: {e}")
            raise EncryptionError(
                "Invalid encryption token or \
        corrupted data",
                {"original_error": str(e)},
            )
        except ValueError as e:
        if "Invalid" in str(e) and ("key" in str(e).lower() or "token" in str(e).lower()):
                logger.error(f"Invalid encryption key/token in {func.__name__}: {e}")
                raise EncryptionError(
                    "Invalid encryption key or \
        token",
                    {"original_error": str(e)},
                )
            raise

        return wrapper


    def safe_int_conversion(value: str, default: int = 0, field_name: str = "value") -> int:

        """Safely convert string to int with specific error handling."""
        try:
        return int(value)
        except (ValueError, TypeError) as e:
        logger.warning(f"Failed to convert {field_name} '{value}' to int: {e}")
        return default


    def safe_json_parse(json_str: str, default: dict = None, field_name: str = "data") -> dict:

        """Safely parse JSON string with specific error handling."""

        if default is None:
        default = {}

        try:
        return json.loads(json_str)
        except (json.JSONDecodeError, TypeError) as e:
        logger.warning(f"Failed to parse JSON {field_name}: {e}")
        return default


    def handle_http_client_exceptions(service_name: str):

        """Decorator to handle HTTP client exceptions."""

    def decorator(func):

    def wrapper(*args, **kwargs):

        try:
        return func(*args, **kwargs)
        except ConnectionError as e:
                logger.error(f"Connection error to {service_name} in {func.__name__}: {e}")
                raise ExternalServiceError(
                    service_name,
                    f"Failed to connect to {service_name}",
                    {"original_error": str(e)},
                )
        except TimeoutError as e:
                logger.error(f"Timeout error to {service_name} in {func.__name__}: {e}")
                raise ExternalServiceError(
                    service_name,
                    f"Timeout connecting to {service_name}",
                    {"original_error": str(e)},
                )
        except Exception as e:
        if "timeout" in str(e).lower():
                    logger.error(f"Timeout error to {service_name} in {func.__name__}: {e}")
                    raise ExternalServiceError(
                        service_name,
                        f"Timeout connecting to {service_name}",
                        {"original_error": str(e)},
                    )
        elif "connection" in str(e).lower():
                    logger.error(f"Connection error to {service_name} in {func.__name__}: {e}")
                    raise ExternalServiceError(
                        service_name,
                        f"Connection error to {service_name}",
                        {"original_error": str(e)},
                    )
                raise

        return wrapper

        return decorator