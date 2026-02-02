"""Comprehensive monitoring system for task 14.3."""


import asyncio
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List

@dataclass
class Metric:

    """Individual metric data point."""

    name: str
    value: float
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    tags: Dict[str, str] = field(default_factory=dict)


class MetricsCollector:

    """Application performance metrics collector."""

    def __init__(self):

        self.metrics = []
        self.counters = {}
        self.gauges = {}

    def increment(self, name: str, value: float = 1.0, tags: Dict[str, str] = None):

        """Increment counter metric."""
        self.counters[name] = self.counters.get(name, 0) + value
        self.metrics.append(Metric(name, value, tags=tags or {}))

    def gauge(self, name: str, value: float, tags: Dict[str, str] = None):

        """Set gauge metric."""
        self.gauges[name] = value
        self.metrics.append(Metric(name, value, tags=tags or {}))

    def timer(self, name: str, duration: float, tags: Dict[str, str] = None):

        """Record timing metric."""
        self.metrics.append(Metric(f"{name}.duration", duration, tags=tags or {}))

    def get_metrics(self) -> List[Metric]:

        """Get all collected metrics."""
        return self.metrics.copy()

    def clear_metrics(self):

        """Clear collected metrics."""
        self.metrics.clear()


class PerformanceMonitor:

        """Performance monitoring and SLA tracking."""

    def __init__(self):

        self.sla_thresholds = {
            "response_time_p95": 2000,  # 2 seconds
            "error_rate": 5.0,  # 5%
            "uptime": 99.9,  # 99.9%
        }
        self.metrics_collector = MetricsCollector()

    async def track_request(self, endpoint: str, method: str, status_code: int, duration: float):
        """Track individual request metrics."""
        tags = {"endpoint": endpoint, "method": method, "status": str(status_code)}

        # Record request
        self.metrics_collector.increment("requests.total", tags=tags)
        self.metrics_collector.timer("requests.duration", duration, tags=tags)

        # Track errors
        if status_code >= 400:
            self.metrics_collector.increment("requests.errors", tags=tags)

    async def check_sla_compliance(self) -> Dict[str, Any]:
        """Check SLA compliance."""
        metrics = self.metrics_collector.get_metrics()

        # Calculate response time percentiles
        response_times = [m.value for m in metrics if m.name == "requests.duration"]
        p95_response_time = self._calculate_percentile(response_times, 95) if response_times else 0

        # Calculate error rate
        total_requests = len([m for m in metrics if m.name == "requests.total"])
        error_requests = len([m for m in metrics if m.name == "requests.errors"])
        error_rate = (error_requests / total_requests * 100) if total_requests > 0 else 0

        # Check compliance
        compliance = {
            "response_time_p95": {
                "value": p95_response_time,
                "threshold": self.sla_thresholds["response_time_p95"],
                "compliant": p95_response_time <= self.sla_thresholds["response_time_p95"],
            },
            "error_rate": {
                "value": error_rate,
                "threshold": self.sla_thresholds["error_rate"],
                "compliant": error_rate <= self.sla_thresholds["error_rate"],
            },
        }

        return compliance

        @staticmethod
    def _calculate_percentile(values: List[float], percentile: int) -> float:

        """Calculate percentile value."""
        if not values:
        return 0

        sorted_values = sorted(values)
        index = int(len(sorted_values) * percentile / 100)
        return sorted_values[min(index, len(sorted_values) - 1)]


class ErrorTracker:

        """Error tracking and alerting system."""

    def __init__(self):

        self.errors = []
        self.alert_thresholds = {
            "error_rate_5min": 10,  # 10 errors in 5 minutes
            "critical_error_rate": 5,  # 5 critical errors
        }

    def track_error(self, error: Exception, context: Dict[str, Any] = None):

        """Track application error."""
        error_data = {
            "timestamp": datetime.now(timezone.utc),
            "type": type(error).__name__,
            "message": str(error),
            "context": context or {},
            "severity": self._determine_severity(error),
        }

        self.errors.append(error_data)

        # Check for alert conditions
        if self._should_alert(error_data):
            asyncio.create_task(self._send_alert(error_data))

        @staticmethod
    def _determine_severity(error: Exception) -> str:

        """Determine error severity."""
        critical_errors = ["DatabaseError", "PaymentError", "ExternalServiceError"]

        if type(error).__name__ in critical_errors:
        return "critical"
        elif "timeout" in str(error).lower():
        return "warning"
        else:
        return "info"

    def _should_alert(self, error_data: Dict) -> bool:

        """Check if error should trigger alert."""
        # Alert on critical errors
        if error_data["severity"] == "critical":
        return True

        # Alert on high error rate
        recent_errors = [e for e in self.errors if (datetime.now(timezone.utc) - e["timestamp"]).seconds < 300]

        return len(recent_errors) >= self.alert_thresholds["error_rate_5min"]

        @staticmethod
    async def _send_alert(error_data: Dict):
        """Send error alert."""
        # In production, integrate with alerting system (PagerDuty, Slack, etc.)
        print(f"ALERT: {error_data['severity'].upper()} error - {error_data['message']}")


class DashboardMetrics:

        """Real - time dashboard metrics."""

    def __init__(self):

        self.performance_monitor = PerformanceMonitor()
        self.error_tracker = ErrorTracker()

    async def get_system_health(self) -> Dict[str, Any]:
        """Get current system health metrics."""
        sla_compliance = await self.performance_monitor.check_sla_compliance()

        # Recent error count
        recent_errors = [
            e for e in self.error_tracker.errors if (datetime.now(timezone.utc) - e["timestamp"]).seconds < 3600
        ]

        return {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "sla_compliance": sla_compliance,
            "error_count_1h": len(recent_errors),
            "critical_errors_1h": len([e for e in recent_errors if e["severity"] == "critical"]),
            "system_status": ("healthy" if all(sla["compliant"] for sla in sla_compliance.values()) else "degraded"),
        }

        @staticmethod
    async def get_business_metrics() -> Dict[str, Any]:
        """Get business metrics."""
        # In production, fetch from database
        return {
            "verifications_today": 150,
            "revenue_today": 75.0,
            "active_users": 45,
            "conversion_rate": 85.5,
            "average_verification_time": 45.2,
        }


class CanaryAnalyzer:

        """Automated canary deployment analysis."""

    def __init__(self):

        self.baseline_metrics = {}
        self.canary_metrics = {}

    def set_baseline(self, metrics: Dict[str, float]):

        """Set baseline metrics for comparison."""
        self.baseline_metrics = metrics.copy()

    def analyze_canary(self, canary_metrics: Dict[str, float]) -> Dict[str, Any]:

        """Analyze canary deployment metrics."""
        self.canary_metrics = canary_metrics.copy()

        analysis = {
            "recommendation": "proceed",
            "confidence": 0.95,
            "metrics_comparison": {},
        }

        # Compare key metrics
        for metric, canary_value in canary_metrics.items():
        if metric in self.baseline_metrics:
                baseline_value = self.baseline_metrics[metric]
                change_percent = ((canary_value - baseline_value) / baseline_value) * 100

                analysis["metrics_comparison"][metric] = {
                    "baseline": baseline_value,
                    "canary": canary_value,
                    "change_percent": change_percent,
                }

                # Check for significant degradation
        if metric == "error_rate" and change_percent > 50:
                    analysis["recommendation"] = "rollback"
                    analysis["confidence"] = 0.9
        elif metric == "response_time" and change_percent > 25:
                    analysis["recommendation"] = "rollback"
                    analysis["confidence"] = 0.85

        return analysis


# Global monitoring instances
        metrics_collector = MetricsCollector()
        performance_monitor = PerformanceMonitor()
        error_tracker = ErrorTracker()
        dashboard_metrics = DashboardMetrics()
        canary_analyzer = CanaryAnalyzer()