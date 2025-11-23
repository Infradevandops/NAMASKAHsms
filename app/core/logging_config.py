"""Logging configuration and utilities."""
import logging
from typing import Optional
from app.core.config import settings


def configure_logging() -> None:
    """Configure application logging."""
    log_level = logging.DEBUG if settings.debug else logging.INFO
    
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler('app.log') if not settings.debug else logging.NullHandler(),
        ]
    )


def get_logger(name: str) -> logging.Logger:
    """Get logger instance."""
    return logging.getLogger(name)


def log_operation(logger: logging.Logger, operation: str, **kwargs) -> None:
    """Log an operation with context."""
    context = ' | '.join(f"{k}={v}" for k, v in kwargs.items())
    logger.info(f"{operation} | {context}")


def log_error(logger: logging.Logger, operation: str, error: Exception, **kwargs) -> None:
    """Log an error with context."""
    context = ' | '.join(f"{k}={v}" for k, v in kwargs.items())
    logger.error(f"{operation} | {context} | Error: {str(error)}")


def log_security_event(logger: logging.Logger, event: str, **kwargs) -> None:
    """Log security-related event."""
    context = ' | '.join(f"{k}={v}" for k, v in kwargs.items())
    logger.warning(f"SECURITY: {event} | {context}")
