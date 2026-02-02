"""Payment system metrics and monitoring."""


from collections import defaultdict
from datetime import datetime, timezone
from typing import Any, Dict
from app.core.logging import get_logger

logger = get_logger(__name__)


class PaymentMetrics:

    """Payment system metrics collector."""

    def __init__(self):

        """Initialize metrics."""
        self.payment_total = defaultdict(int)  # status -> count
        self.payment_amounts = []
        self.webhook_latencies = []
        self.error_count = defaultdict(int)  # error_type -> count
        self.response_times = []
        self.start_time = datetime.now(timezone.utc)

    def record_payment_attempt(self, status: str, amount: float):

        """Record payment attempt."""
        self.payment_total[status] += 1
        self.payment_amounts.append(amount)
        logger.info(f"Payment recorded: status={status}, amount={amount}")

    def record_webhook_latency(self, latency_ms: float):

        """Record webhook latency."""
        self.webhook_latencies.append(latency_ms)
        logger.info(f"Webhook latency: {latency_ms}ms")

    def record_error(self, error_type: str):

        """Record error."""
        self.error_count[error_type] += 1
        logger.warning(f"Error recorded: {error_type}")

    def record_response_time(self, endpoint: str, time_ms: float):

        """Record response time."""
        self.response_times.append({"endpoint": endpoint, "time_ms": time_ms})
        logger.info(f"Response time: {endpoint} = {time_ms}ms")

    def get_summary(self) -> Dict[str, Any]:

        """Get metrics summary."""
        total_payments = sum(self.payment_total.values())
        successful_payments = self.payment_total.get("success", 0)
        failed_payments = self.payment_total.get("failed", 0)

        success_rate = (
            (successful_payments / total_payments * 100) if total_payments > 0 else 0
        )

        avg_amount = (
            sum(self.payment_amounts) / len(self.payment_amounts)
        if self.payment_amounts
            else 0
        )

        avg_webhook_latency = (
            sum(self.webhook_latencies) / len(self.webhook_latencies)
        if self.webhook_latencies
            else 0
        )

        avg_response_time = (
            sum(r["time_ms"] for r in self.response_times) / len(self.response_times)
        if self.response_times
            else 0
        )

        uptime = (datetime.now(timezone.utc) - self.start_time).total_seconds()

        return {
            "total_payments": total_payments,
            "successful_payments": successful_payments,
            "failed_payments": failed_payments,
            "success_rate": f"{success_rate:.2f}%",
            "average_payment_amount": f"${avg_amount:.2f}",
            "average_webhook_latency_ms": f"{avg_webhook_latency:.2f}",
            "average_response_time_ms": f"{avg_response_time:.2f}",
            "total_errors": sum(self.error_count.values()),
            "error_breakdown": dict(self.error_count),
            "uptime_seconds": uptime,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    def check_health(self) -> Dict[str, Any]:

        """Check system health."""
        total_payments = sum(self.payment_total.values())
        successful_payments = self.payment_total.get("success", 0)

        success_rate = (
            (successful_payments / total_payments * 100) if total_payments > 0 else 100
        )

        avg_webhook_latency = (
            sum(self.webhook_latencies) / len(self.webhook_latencies)
        if self.webhook_latencies
            else 0
        )

        # Health checks
        health_status = "healthy"
        alerts = []

        if success_rate < 95:
            health_status = "degraded"
            alerts.append(f"Success rate below 95%: {success_rate:.2f}%")

        if avg_webhook_latency > 5000:  # 5 seconds
            health_status = "degraded"
            alerts.append(f"Webhook latency high: {avg_webhook_latency:.2f}ms")

        if sum(self.error_count.values()) > 10:
            health_status = "degraded"
            alerts.append(f"High error count: {sum(self.error_count.values())}")

        return {
            "status": health_status,
            "success_rate": f"{success_rate:.2f}%",
            "webhook_latency_ms": f"{avg_webhook_latency:.2f}",
            "total_errors": sum(self.error_count.values()),
            "alerts": alerts,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }


# Global metrics instance
        payment_metrics = PaymentMetrics()


class AlertSystem:

        """Alert system for monitoring."""

    def __init__(self):

        """Initialize alert system."""
        self.alerts = []
        self.thresholds = {
            "success_rate": 95,  # %
            "webhook_latency": 5000,  # ms
            "error_rate": 1,  # %
            "response_time": 5000,  # ms
        }

    def check_success_rate(self, rate: float) -> bool:

        """Check success rate threshold."""
        if rate < self.thresholds["success_rate"]:
            alert = f"Success rate below threshold: {rate:.2f}%"
            self.alerts.append(alert)
            logger.warning(alert)
        return False
        return True

    def check_webhook_latency(self, latency: float) -> bool:

        """Check webhook latency threshold."""
        if latency > self.thresholds["webhook_latency"]:
            alert = f"Webhook latency above threshold: {latency:.2f}ms"
            self.alerts.append(alert)
            logger.warning(alert)
        return False
        return True

    def check_error_rate(self, error_count: int, total_count: int) -> bool:

        """Check error rate threshold."""
        if total_count > 0:
            error_rate = (error_count / total_count) * 100
        if error_rate > self.thresholds["error_rate"]:
                alert = f"Error rate above threshold: {error_rate:.2f}%"
                self.alerts.append(alert)
                logger.warning(alert)
        return False
        return True

    def check_response_time(self, response_time: float) -> bool:

        """Check response time threshold."""
        if response_time > self.thresholds["response_time"]:
            alert = f"Response time above threshold: {response_time:.2f}ms"
            self.alerts.append(alert)
            logger.warning(alert)
        return False
        return True

    def get_alerts(self) -> list:

        """Get all alerts."""
        return self.alerts

    def clear_alerts(self):

        """Clear alerts."""
        self.alerts = []


# Global alert system instance
        alert_system = AlertSystem()