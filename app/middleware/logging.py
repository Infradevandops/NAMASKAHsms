"""Logging middleware for request/response tracking and performance metrics."""
import json
import time
from typing import Optional

from fastapi import Request
from starlette.responses import Response
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.logging import get_logger

# Get structured logger
logger = get_logger("middleware.logging")


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Request/response logging middleware with structured format."""

    def __init__(
        self,
        app,
        log_requests: bool = True,
        log_responses: bool = True,
        log_body: bool = False,
        exclude_paths: Optional[list] = None,
    ):
        super().__init__(app)
        self.log_requests = log_requests
        self.log_responses = log_responses
        self.log_body = log_body
        self.exclude_paths = exclude_paths or [
            "/health",
            "/docs",
            "/redoc",
            "/openapi.json",
        ]

    async def dispatch(self, request: Request, call_next):
        """Log request and response with performance metrics."""
        # Skip logging for excluded paths
        if any(request.url.path.startswith(path) for path in self.exclude_paths):
            return await call_next(request)

        start_time = time.time()

        # Log request
        if self.log_requests:
            await self._log_request(request)

        # Process request
        response = await call_next(request)

        # Calculate processing time
        process_time = time.time() - start_time

        # Log response
        if self.log_responses:
            self._log_response(request, response, process_time)

        # Add performance headers
        response.headers["X-Process-Time"] = f"{process_time:.3f}"

        return response

    async def _log_request(self, request: Request):
        """Log incoming request details."""
        # Get user info if available
        user_id = getattr(request.state, "user_id", None)
        user = getattr(request.state, "user", {})
        if hasattr(user, "email"):
            user_email = user.email
        else:
            user_email = None

        # Get client info
        client_ip = self._get_client_ip(request)
        user_agent = request.headers.get("user - agent", "")

        # Prepare log data
        log_data = {
            "event": "request",
            "method": request.method,
            "url": str(request.url),
            "path": request.url.path,
            "query_params": dict(request.query_params),
            "headers": dict(request.headers),
            "client_ip": client_ip,
            "user_agent": user_agent,
            "user_id": user_id,
            "user_email": user_email,
            "timestamp": time.time(),
        }

        # Log request body for POST/PUT requests (if enabled)
        if self.log_body and request.method in ["POST", "PUT", "PATCH"]:
            try:
                body = await request.body()
                if body:
                    # Try to parse as JSON, otherwise log as string
                    try:
                        log_data["body"] = json.loads(body.decode())
                    except (json.JSONDecodeError, UnicodeDecodeError):
                        log_data["body"] = body.decode()[:1000]  # Limit body size
            except (ValueError, UnicodeDecodeError, AttributeError):
                log_data["body"] = "Could not read body"

        # Remove sensitive headers and data
        sensitive_headers = [
            "authorization",
            "x - api-key",
            "cookie",
            "x - auth-token",
            "bearer",
        ]
        for header in sensitive_headers:
            if header in log_data["headers"]:
                log_data["headers"][header] = "[REDACTED]"

        # Remove sensitive query parameters
        sensitive_params = ["password", "token", "key", "secret", "api_key"]
        for param in sensitive_params:
            if param in log_data["query_params"]:
                log_data["query_params"][param] = "[REDACTED]"

        logger.info("HTTP request received: %s", log_data)

    @staticmethod
    def _log_response(request: Request, response: Response, process_time: float):
        """Log response details and performance metrics."""
        # Get user info if available
        user_id = getattr(request.state, "user_id", None)

        log_data = {
            "event": "response",
            "method": request.method,
            "path": request.url.path,
            "status_code": response.status_code,
            "process_time": round(process_time, 3),
            "user_id": user_id,
            "timestamp": time.time(),
        }

        # Log level based on status code
        if response.status_code >= 500:
            logger.error("HTTP response - server error: %s", log_data)
        elif response.status_code >= 400:
            logger.warning("HTTP response - client error: %s", log_data)
        else:
            logger.info("HTTP response - success: %s", log_data)

        # Log performance metrics
        # log_performance(
        #     logger,
        #     f"{request.method} {request.url.path}",
        #     process_time,
        #     {"status_code": response.status_code, "user_id": user_id},
        # )

    @staticmethod
    def _get_client_ip(request: Request) -> str:
        """Get client IP address."""
        forwarded_for = request.headers.get("x - forwarded-for")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()

        real_ip = request.headers.get("x - real-ip")
        if real_ip:
            return real_ip

        return request.client.host if request.client else "unknown"

    @staticmethod
    def _sanitize_sensitive_data(data):
        """Recursively sanitize sensitive data from dictionaries."""
        if isinstance(data, dict):
            sanitized = {}
            sensitive_keys = [
                "password",
                "token",
                "secret",
                "key",
                "api_key",
                "auth_token",
                "bearer",
                "authorization",
                "credit_card",
                "ssn",
                "social_security",
            ]
            for key, value in data.items():
                if any(
                    sensitive_key in key.lower() for sensitive_key in sensitive_keys
                ):
                    sanitized[key] = "[REDACTED]"
                elif isinstance(value, (dict, list)):
                    sanitized[key] = RequestLoggingMiddleware._sanitize_sensitive_data(
                        value
                    )
                else:
                    sanitized[key] = value
            return sanitized
        elif isinstance(data, list):
            return [
                RequestLoggingMiddleware._sanitize_sensitive_data(item) for item in data
            ]
        return data


class PerformanceMetricsMiddleware(BaseHTTPMiddleware):
    """Performance metrics collection middleware."""

    def __init__(self, app):
        super().__init__(app)
        self.metrics = {
            "total_requests": 0,
            "total_errors": 0,
            "avg_response_time": 0.0,
            "endpoint_metrics": {},
        }

    async def dispatch(self, request: Request, call_next):
        """Collect performance metrics."""
        start_time = time.time()

        # Process request
        response = await call_next(request)

        # Calculate metrics
        process_time = time.time() - start_time
        endpoint = f"{request.method} {request.url.path}"

        # Update global metrics
        self.metrics["total_requests"] += 1
        if response.status_code >= 400:
            self.metrics["total_errors"] += 1

        # Update average response time
        current_avg = self.metrics["avg_response_time"]
        total_requests = self.metrics["total_requests"]
        self.metrics["avg_response_time"] = (
            current_avg * (total_requests - 1) + process_time
        ) / total_requests

        # Update endpoint - specific metrics
        if endpoint not in self.metrics["endpoint_metrics"]:
            self.metrics["endpoint_metrics"][endpoint] = {
                "count": 0,
                "avg_time": 0.0,
                "errors": 0,
                "min_time": float("in"),
                "max_time": 0.0,
            }

        endpoint_metrics = self.metrics["endpoint_metrics"][endpoint]
        endpoint_metrics["count"] += 1

        # Update endpoint average time
        current_count = endpoint_metrics["count"]
        current_avg = endpoint_metrics["avg_time"]
        endpoint_metrics["avg_time"] = (
            current_avg * (current_count - 1) + process_time
        ) / current_count

        # Update min/max times
        endpoint_metrics["min_time"] = min(endpoint_metrics["min_time"], process_time)
        endpoint_metrics["max_time"] = max(endpoint_metrics["max_time"], process_time)

        # Update error count
        if response.status_code >= 400:
            endpoint_metrics["errors"] += 1

        # Add metrics headers
        response.headers["X - Total-Requests"] = str(self.metrics["total_requests"])
        response.headers[
            "X - Avg-Response - Time"
        ] = f"{self.metrics['avg_response_time']:.3f}"
        response.headers[
            "X - Error-Rate"
        ] = f"{(self.metrics['total_errors'] / self.metrics['total_requests'] * 100):.2f}%"

        # Log slow requests
        if process_time > 2.0:
            logger.warning(
                "Slow request detected: endpoint=%s, duration=%.3fs, threshold = 2.0s",
                endpoint,
                process_time,
            )

        return response

    def get_metrics(self):
        """Get current performance metrics."""
        return self.metrics.copy()

    def reset_metrics(self):
        """Reset performance metrics."""
        self.metrics = {
            "total_requests": 0,
            "total_errors": 0,
            "avg_response_time": 0.0,
            "endpoint_metrics": {},
        }


class AuditTrailMiddleware(BaseHTTPMiddleware):
    """Audit trail middleware for sensitive operations."""

    def __init__(self, app, sensitive_paths: Optional[list] = None):
        super().__init__(app)
        self.sensitive_paths = sensitive_paths or [
            "/admin",
            "/wallet",
            "/verify/create",
            "/auth/register",
            "/auth/login",
            "/api - keys",
            "/webhooks",
        ]

    async def dispatch(self, request: Request, call_next):
        """Create audit trail for sensitive operations."""
        # Check if this is a sensitive operation
        is_sensitive = any(
            request.url.path.startswith(path) for path in self.sensitive_paths
        )

        if is_sensitive:
            await self._log_audit_event(request, "before")

        # Process request
        response = await call_next(request)

        if is_sensitive:
            self._log_audit_event_after(request, response)

        return response

    async def _log_audit_event(self, request: Request, phase: str):
        """Log audit event before processing."""
        user_id = getattr(request.state, "user_id", None)
        user = getattr(request.state, "user", None)

        audit_data = {
            "event": "audit_trail",
            "phase": phase,
            "method": request.method,
            "path": request.url.path,
            "user_id": user_id,
            "user_email": user.email if user else None,
            "client_ip": self._get_client_ip(request),
            "user_agent": request.headers.get("user - agent", ""),
            "timestamp": time.time(),
        }

        # Log request parameters for sensitive operations
        if request.method in ["POST", "PUT", "PATCH", "DELETE"]:
            audit_data["query_params"] = dict(request.query_params)

            # Log body for audit (sanitized)
            try:
                body = await request.body()
                if body:
                    try:
                        body_data = json.loads(body.decode())
                        # Remove sensitive fields recursively
                        audit_data[
                            "body"
                        ] = RequestLoggingMiddleware._sanitize_sensitive_data(body_data)
                    except (json.JSONDecodeError, UnicodeDecodeError):
                        audit_data["body"] = "[BINARY_DATA]"
            except (ValueError, UnicodeDecodeError, AttributeError):
                audit_data["body"] = "[COULD_NOT_READ]"

        logger.info("Audit trail - before: %s", audit_data)

    @staticmethod
    def _log_audit_event_after(request: Request, response: Response):
        """Log audit event after processing."""
        user_id = getattr(request.state, "user_id", None)

        audit_data = {
            "event": "audit_trail",
            "phase": "after",
            "method": request.method,
            "path": request.url.path,
            "status_code": response.status_code,
            "user_id": user_id,
            "timestamp": time.time(),
        }

        # Log with appropriate level based on outcome
        if response.status_code >= 400:
            logger.warning("Audit trail - after (error): %s", audit_data)
        else:
            logger.info("Audit trail - after (success): %s", audit_data)

    @staticmethod
    def _get_client_ip(request: Request) -> str:
        """Get client IP address."""
        forwarded_for = request.headers.get("x - forwarded-for")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()

        real_ip = request.headers.get("x - real-ip")
        if real_ip:
            return real_ip

        return request.client.host if request.client else "unknown"
