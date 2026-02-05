"""
import time
from collections import Counter, defaultdict
from typing import Any, Dict
import psutil
from prometheus_client import CONTENT_TYPE_LATEST
from app.core.config import settings
from app.core.logging import get_logger, log_business_event, log_performance
import re

Production Metrics Collection System
Prometheus - compatible metrics for monitoring and alerting.
"""


logger = get_logger("metrics")

# Prometheus metrics
REQUEST_COUNT = PrometheusCounter("http_requests_total", "Total HTTP requests", ["method", "endpoint", "status_code"])

REQUEST_DURATION = Histogram(
    "http_request_duration_seconds",
    "HTTP request duration in seconds",
    ["method", "endpoint"],
)

ACTIVE_CONNECTIONS = Gauge("active_connections_total", "Number of active connections")

DATABASE_CONNECTIONS = Gauge("database_connections_active", "Active database connections")

REDIS_CONNECTIONS = Gauge("redis_connections_active", "Active Redis connections")

BUSINESS_EVENTS = PrometheusCounter("business_events_total", "Business events counter", ["event_type", "status"])

ERROR_COUNT = PrometheusCounter("errors_total", "Total errors", ["error_type", "severity"])

SYSTEM_CPU = Gauge("system_cpu_usage_percent", "System CPU usage percentage")

SYSTEM_MEMORY = Gauge("system_memory_usage_percent", "System memory usage percentage")

SYSTEM_DISK = Gauge("system_disk_usage_percent", "System disk usage percentage")


class MetricsCollector:

    """Centralized metrics collection and management."""

    def __init__(self):

        self.start_time = time.time()
        self.request_stats = defaultdict(lambda: {"count": 0, "total_time": 0})
        self.error_stats = Counter()
        self.business_stats = Counter()

    def record_request(self, method: str, endpoint: str, status_code: int, duration: float):

        """Record HTTP request metrics."""
        # Prometheus metrics
        REQUEST_COUNT.labels(method=method, endpoint=endpoint, status_code=status_code).inc()
        REQUEST_DURATION.labels(method=method, endpoint=endpoint).observe(duration)

        # Internal stats
        key = f"{method}:{endpoint}"
        self.request_stats[key]["count"] += 1
        self.request_stats[key]["total_time"] += duration

        logger.debug(
            "Request recorded",
            method=method,
            endpoint=endpoint,
            status_code=status_code,
            duration_ms=duration * 1000,
        )

    def record_error(self, error_type: str, severity: str = "medium"):

        """Record error metrics."""
        ERROR_COUNT.labels(error_type=error_type, severity=severity).inc()
        self.error_stats[f"{error_type}:{severity}"] += 1

        logger.info("Error recorded", error_type=error_type, severity=severity)

    def record_business_event(self, event_type: str, status: str = "success"):

        """Record business event metrics."""
        BUSINESS_EVENTS.labels(event_type=event_type, status=status).inc()
        self.business_stats[f"{event_type}:{status}"] += 1

        logger.info("Business event recorded", event_type=event_type, status=status)

        @staticmethod
    def update_system_metrics():

        """Update system resource metrics."""
        try:
            # CPU usage
            cpu_percent = psutil.cpu_percent(interval=1)
            SYSTEM_CPU.set(cpu_percent)

            # Memory usage
            memory = psutil.virtual_memory()
            SYSTEM_MEMORY.set(memory.percent)

            # Disk usage
            disk = psutil.disk_usage("/")
            SYSTEM_DISK.set(disk.percent)

            logger.debug(
                "System metrics updated",
                cpu_percent=cpu_percent,
                memory_percent=memory.percent,
                disk_percent=disk.percent,
            )

        except Exception as e:
            logger.error("Failed to update system metrics", error=str(e))
            # Continue execution instead of raising

    def get_application_metrics(self) -> Dict[str, Any]:

        """Get application - specific metrics."""
        uptime = time.time() - self.start_time

        # Calculate request statistics
        total_requests = sum(stats["count"] for stats in self.request_stats.values())
        avg_response_time = 0
        if total_requests > 0:
            total_time = sum(stats["total_time"] for stats in self.request_stats.values())
            avg_response_time = total_time / total_requests

        return {
            "uptime_seconds": uptime,
            "total_requests": total_requests,
            "average_response_time": avg_response_time,
            "error_count": sum(self.error_stats.values()),
            "business_events": sum(self.business_stats.values()),
            "requests_per_second": total_requests / uptime if uptime > 0 else 0,
        }

    def get_health_score(self) -> Dict[str, Any]:

        """Calculate overall health score."""
        try:
            # Get system metrics
            cpu_percent = psutil.cpu_percent()
            memory_percent = psutil.virtual_memory().percent
            disk_percent = psutil.disk_usage("/").percent

            # Calculate health score (0 - 100)
            health_score = 100

            # Deduct points for high resource usage
        if cpu_percent > 80:
                health_score -= 20
        elif cpu_percent > 60:
                health_score -= 10

        if memory_percent > 85:
                health_score -= 20
        elif memory_percent > 70:
                health_score -= 10

        if disk_percent > 90:
                health_score -= 15
        elif disk_percent > 80:
                health_score -= 5

            # Deduct points for errors
            app_metrics = self.get_application_metrics()
            error_rate = 0
        if app_metrics["total_requests"] > 0:
                error_rate = app_metrics["error_count"] / app_metrics["total_requests"]

        if error_rate > 0.05:  # 5% error rate
                health_score -= 25
        elif error_rate > 0.01:  # 1% error rate
                health_score -= 10

            # Deduct points for slow response times
        if app_metrics["average_response_time"] > 2.0:
                health_score -= 15
        elif app_metrics["average_response_time"] > 1.0:
                health_score -= 5

            health_score = max(0, health_score)

        return {
                "health_score": health_score,
                "status": ("healthy" if health_score >= 80 else "degraded" if health_score >= 60 else "unhealthy"),
                "factors": {
                    "cpu_usage": cpu_percent,
                    "memory_usage": memory_percent,
                    "disk_usage": disk_percent,
                    "error_rate": error_rate,
                    "avg_response_time": app_metrics["average_response_time"],
                },
            }

        except Exception as e:
            logger.error("Failed to calculate health score", error=str(e))
        return {"health_score": 0, "status": "unknown", "error": str(e)}


# Global metrics collector instance
        metrics_collector = MetricsCollector()


class MetricsMiddleware:

        """Middleware to collect request metrics."""

    def __init__(self, app):

        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        start_time = time.time()

        # Extract request info
        method = scope["method"]
        path = scope["path"]

        # Normalize endpoint for metrics (remove IDs, etc.)
        normalized_path = MetricsMiddleware._normalize_path(path)

    async def send_wrapper(message):
        if message["type"] == "http.response.start":
                # Record metrics when response starts
                duration = time.time() - start_time
                status_code = message["status"]

                metrics_collector.record_request(method, normalized_path, status_code, duration)

                # Update active connections
                ACTIVE_CONNECTIONS.inc()

            await send(message)

        try:
            await self.app(scope, receive, send_wrapper)
        except Exception as e:
            # Record error
            metrics_collector.record_error(type(e).__name__, "high")
            raise
        finally:
            # Decrease active connections
            ACTIVE_CONNECTIONS.dec()

        @staticmethod
    def _normalize_path(path: str) -> str:

        """Normalize path for metrics grouping."""
        # Replace UUIDs and IDs with placeholders

        # Replace UUIDs
        path = re.sub(
            r"/[0 - 9a-f]{8}-[0 - 9a-f]{4}-[0 - 9a-f]{4}-[0 - 9a-f]{4}-[0 - 9a-f]{12}",
            "/{uuid}",
            path,
        )

        # Replace numeric IDs
        path = re.sub(r"/\d+", "/{id}", path)

        # Replace verification codes
        path = re.sub(r"/[A - Z0-9]{6,}", "/{code}", path)

        return path


    def get_prometheus_metrics() -> str:

        """Get Prometheus - formatted metrics."""
    # Update system metrics before generating output
        metrics_collector.update_system_metrics()

        return generate_latest()


    def get_metrics_content_type() -> str:

        """Get Prometheus metrics content type."""
        return CONTENT_TYPE_LATEST


    async def record_business_event(event_type: str, status: str = "success", **kwargs):
        """Record a business event with additional context."""
        metrics_collector.record_business_event(event_type, status)

    # Log business event for analytics

        business_logger = get_logger("business")
        log_business_event(business_logger, event_type, {"status": status, **kwargs})


    async def record_performance_metric(operation: str, duration: float, **kwargs):
        """Record performance metrics."""
    # Create operation - specific histogram if needed
        operation_histogram = Histogram("operation_duration_seconds", "Operation duration in seconds", ["operation"])

        operation_histogram.labels(operation=operation).observe(duration)

    # Log performance

        performance_logger = get_logger("performance")
        log_performance(performance_logger, operation, duration, kwargs)


class DatabaseMetrics:

        """Database - specific metrics collection."""

        @staticmethod
    def record_query(query_type: str, duration: float, success: bool = True):

        """Record database query metrics."""
        query_histogram = Histogram(
            "database_query_duration_seconds",
            "Database query duration",
            ["query_type", "status"],
        )

        status = "success" if success else "error"
        query_histogram.labels(query_type=query_type, status=status).observe(duration)

        if not success:
            metrics_collector.record_error("database_query", "medium")

        @staticmethod
    def update_connection_count(active_connections: int):

        """Update database connection count."""
        DATABASE_CONNECTIONS.set(active_connections)


class CacheMetrics:

        """Cache - specific metrics collection."""

    def __init__(self):

        self.hit_counter = PrometheusCounter("cache_hits_total", "Cache hits")
        self.miss_counter = PrometheusCounter("cache_misses_total", "Cache misses")
        self.operation_histogram = Histogram(
            "cache_operation_duration_seconds",
            "Cache operation duration",
            ["operation"],
        )

    def record_hit(self):

        """Record cache hit."""
        self.hit_counter.inc()

    def record_miss(self):

        """Record cache miss."""
        self.miss_counter.inc()

    def record_operation(self, operation: str, duration: float):

        """Record cache operation."""
        self.operation_histogram.labels(operation=operation).observe(duration)


# Global cache metrics instance
        cache_metrics = CacheMetrics()


    def get_application_info() -> Dict[str, Any]:

        """Get application information for metrics."""
        return {
        "name": settings.app_name,
        "version": settings.app_version,
        "environment": settings.environment,
        "start_time": metrics_collector.start_time,
        "uptime": time.time() - metrics_collector.start_time,
        }
