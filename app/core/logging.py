"""Enhanced structured logging configuration for production."""
import logging
import os
import sys
import threading
import uuid
from contextvars import ContextVar
from typing import Any, Dict, Optional

from app.core.config import settings

# Context variables for request tracking
correlation_id_var: ContextVar[Optional[str]] = ContextVar(
    "correlation_id", default=None
)
user_id_var: ContextVar[Optional[str]] = ContextVar("user_id", default=None)


class CorrelationIDProcessor:
    """Add correlation ID to log entries."""

    def __call__(self, logger, method_name, event_dict):
        correlation_id = correlation_id_var.get()
        if correlation_id:
            event_dict["correlation_id"] = correlation_id

        user_id = user_id_var.get()
        if user_id:
            event_dict["user_id"] = user_id

        return event_dict


class ProductionMetadataProcessor:
    """Add production metadata to log entries."""

    def __call__(self, logger, method_name, event_dict):
        # Add service metadata
        event_dict.update(
            {
                "service": "namaskah - sms",
                "version": settings.app_version,
                "environment": settings.environment,
                "thread_id": threading.get_ident(),
            }
        )

        # Add request context if available
        if hasattr(threading.current_thread(), "request_context"):
            context = threading.current_thread().request_context
            event_dict.update(
                {
                    "request_method": context.get("method"),
                    "request_path": context.get("path"),
                    "request_ip": context.get("ip"),
                    "user_agent": context.get("user_agent"),
                }
            )

        return event_dict


def setup_logging():
    """Configure basic logging temporarily for debugging."""
    # Set log level based on environment
    log_level = logging.INFO if settings.environment == "production" else logging.DEBUG

    # Configure basic root logger only
    logging.basicConfig(
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        stream=sys.stdout,
        level=log_level,
        force=True,
    )

    # Silence noisy loggers in production
    if settings.environment == "production":
        logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
        logging.getLogger("httpx").setLevel(logging.WARNING)
        logging.getLogger("httpcore").setLevel(logging.WARNING)

    # Skip structlog configuration temporarily
    print("Basic logging configured (structlog disabled for debugging)")


def setup_log_rotation():
    """Setup log rotation for production."""
    import tempfile

    # Use secure log directory - prefer app directory or secure temp
    log_dir = os.environ.get("LOG_DIR")

    if not log_dir:
        # Try app directory first
        try:
            app_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            log_dir = os.path.join(app_dir, "logs")
            os.makedirs(log_dir, mode=0o750, exist_ok=True)
        except OSError:
            # Fallback to secure temp directory
            log_dir = tempfile.mkdtemp(prefix="namaskah_logs_")
    else:
        # Create logs directory with secure permissions
        os.makedirs(log_dir, mode=0o750, exist_ok=True)

    # Setup rotating file handler
    file_handler = RotatingFileHandler(
        os.path.join(log_dir, "app.log"),
        maxBytes=100 * 1024 * 1024,  # 100MB
        backupCount=10,
    )
    file_handler.setLevel(logging.INFO)

    # Add to root logger
    root_logger = logging.getLogger()
    root_logger.addHandler(file_handler)


def get_logger(name: str = None):
    """Get basic logger instance."""
    return logging.getLogger(name or __name__)


def set_correlation_id(correlation_id: str = None):
    """Set correlation ID for request tracking."""
    if correlation_id is None:
        correlation_id = str(uuid.uuid4())
    correlation_id_var.set(correlation_id)
    return correlation_id


def set_user_context(user_id: str):
    """Set user context for logging."""
    user_id_var.set(user_id)


def clear_context():
    """Clear logging context."""
    correlation_id_var.set(None)
    user_id_var.set(None)


def log_error(logger, error: Exception, context: dict = None):
    """Log error with full context and stack trace."""
    error_context = {
        "error_type": type(error).__name__,
        "error_message": str(error),
        "error_module": error.__class__.__module__,
        "severity": "error",
    }

    if context:
        error_context.update(context)

    logger.error("Exception occurred", extra=error_context, exc_info=True)


def log_performance(logger, operation: str, duration: float, context: dict = None):
    """Log performance metrics with enhanced categorization."""
    perf_context = {
        "operation": operation,
        "duration_ms": round(duration * 1000, 2),
        "metric_type": "performance",
    }

    # Categorize performance
    if duration > 5.0:
        perf_context["performance_category"] = "critical"
        log_level = "error"
    elif duration > 2.0:
        perf_context["performance_category"] = "slow"
        log_level = "warning"
    elif duration > 1.0:
        perf_context["performance_category"] = "moderate"
        log_level = "info"
    else:
        perf_context["performance_category"] = "fast"
        log_level = "debug"

    if context:
        perf_context.update(context)

    # Log at appropriate level
    getattr(logger, log_level)("Operation performance", extra=perf_context)


def log_business_event(logger, event_type: str, event_data: Dict[str, Any]):
    """Log business events for analytics."""
    from datetime import datetime, timezone

    business_context = {
        "event_type": event_type,
        "metric_type": "business",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    # Avoid 'event' key conflicts by filtering it out
    safe_event_data = {k: v for k, v in event_data.items() if k != "event"}
    business_context.update(safe_event_data)

    logger.info("Business event", extra=business_context)


def log_security_event(logger, event_type: str, severity: str, details: Dict[str, Any]):
    """Log security events."""
    security_context = {
        "event_type": event_type,
        "severity": severity,
        "metric_type": "security",
        "requires_attention": severity in ["high", "critical"],
    }
    # Avoid 'event' key conflicts by filtering it out
    safe_details = {k: v for k, v in details.items() if k != "event"}
    security_context.update(safe_details)

    if severity in ["high", "critical"]:
        logger.error("Security event", extra=security_context)
    elif severity == "medium":
        logger.warning("Security event", extra=security_context)
    else:
        logger.info("Security event", extra=security_context)


def log_api_request(
    logger,
    method: str,
    path: str,
    status_code: int,
    duration: float,
    user_id: str = None,
    ip: str = None,
):
    """Log API request with standardized format."""
    request_context = {
        "method": method,
        "path": path,
        "status_code": status_code,
        "duration_ms": round(duration * 1000, 2),
        "metric_type": "api_request",
    }

    if user_id:
        request_context["user_id"] = user_id
    if ip:
        request_context["client_ip"] = ip

    # Determine log level based on status code
    if status_code >= 500:
        log_level = "error"
    elif status_code >= 400:
        log_level = "warning"
    else:
        log_level = "info"

    getattr(logger, log_level)("API request", extra=request_context)
