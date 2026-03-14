"""TextVerified API health monitoring."""

import time
from datetime import datetime, timezone
from typing import Dict, Any

from app.core.logging import get_logger
from app.services.textverified_service import TextVerifiedService

logger = get_logger(__name__)


class TextVerifiedHealthMonitor:
    """Monitor TextVerified API health and performance."""

    def __init__(self):
        self.tv_service = TextVerifiedService()
        self.last_check = None
        self.last_status = None
        self.response_times = []
        self.error_count = 0
        self.success_count = 0

    async def check_health(self) -> Dict[str, Any]:
        """Check TextVerified API health status.
        
        Returns:
            {
                "status": "healthy" | "degraded" | "unhealthy",
                "enabled": bool,
                "response_time_ms": float,
                "last_check": datetime,
                "success_count": int,
                "error_count": int,
                "avg_response_time_ms": float,
                "p95_response_time_ms": float,
            }
        """
        start_time = time.time()
        
        try:
            if not self.tv_service.enabled:
                return {
                    "status": "unhealthy",
                    "enabled": False,
                    "reason": "TextVerified service not configured",
                    "last_check": datetime.now(timezone.utc),
                }

            # Test API connectivity with balance check
            balance_result = await self.tv_service.get_balance()
            
            response_time_ms = (time.time() - start_time) * 1000
            self.response_times.append(response_time_ms)
            self.success_count += 1
            
            # Keep only last 100 response times
            if len(self.response_times) > 100:
                self.response_times.pop(0)

            # Determine health status
            if response_time_ms > 5000:
                status = "degraded"
            else:
                status = "healthy"

            avg_response_time = sum(self.response_times) / len(self.response_times)
            p95_response_time = sorted(self.response_times)[int(len(self.response_times) * 0.95)] if self.response_times else 0

            self.last_check = datetime.now(timezone.utc)
            self.last_status = status

            logger.info(
                f"TextVerified health check: status={status}, "
                f"response_time={response_time_ms:.0f}ms, "
                f"balance={balance_result.get('balance', 'unknown')}"
            )

            return {
                "status": status,
                "enabled": True,
                "response_time_ms": round(response_time_ms, 2),
                "last_check": self.last_check,
                "success_count": self.success_count,
                "error_count": self.error_count,
                "avg_response_time_ms": round(avg_response_time, 2),
                "p95_response_time_ms": round(p95_response_time, 2),
                "balance": balance_result.get("balance"),
            }

        except Exception as e:
            response_time_ms = (time.time() - start_time) * 1000
            self.error_count += 1
            
            logger.error(f"TextVerified health check failed: {str(e)}", exc_info=True)

            return {
                "status": "unhealthy",
                "enabled": True,
                "error": str(e),
                "response_time_ms": round(response_time_ms, 2),
                "last_check": datetime.now(timezone.utc),
                "success_count": self.success_count,
                "error_count": self.error_count,
            }

    def get_metrics(self) -> Dict[str, Any]:
        """Get current health metrics."""
        if not self.response_times:
            return {
                "status": "unknown",
                "success_count": 0,
                "error_count": 0,
                "avg_response_time_ms": 0,
            }

        avg_response_time = sum(self.response_times) / len(self.response_times)
        p95_response_time = sorted(self.response_times)[int(len(self.response_times) * 0.95)]
        
        # Determine overall status
        if self.error_count > self.success_count:
            status = "unhealthy"
        elif avg_response_time > 3000:
            status = "degraded"
        else:
            status = "healthy"

        return {
            "status": status,
            "success_count": self.success_count,
            "error_count": self.error_count,
            "success_rate": round(
                (self.success_count / (self.success_count + self.error_count) * 100)
                if (self.success_count + self.error_count) > 0
                else 0,
                2
            ),
            "avg_response_time_ms": round(avg_response_time, 2),
            "p95_response_time_ms": round(p95_response_time, 2),
            "last_check": self.last_check,
        }


# Global instance
_health_monitor = TextVerifiedHealthMonitor()


def get_health_monitor() -> TextVerifiedHealthMonitor:
    """Get global health monitor instance."""
    return _health_monitor
