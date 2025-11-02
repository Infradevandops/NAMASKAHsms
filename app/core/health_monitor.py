"""Health monitoring for external services."""
import asyncio
import time
from typing import Dict, Any, List
from dataclasses import dataclass
from enum import Enum
from app.core.logging import get_logger
from app.services.textverified_client import textverified_client

logger = get_logger(__name__)

class ServiceStatus(Enum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"

@dataclass
class HealthCheck:
    service: str
    status: ServiceStatus
    response_time: float
    last_check: float
    error: str = None

class HealthMonitor:
    """Monitor health of external services."""
    
    def __init__(self):
        self.checks: Dict[str, HealthCheck] = {}
        self.check_interval = 60  # 1 minute
        self.running = False
        
    async def check_textverified_health(self) -> HealthCheck:
        """Check TextVerified API health."""
        start_time = time.time()
        
        try:
            is_healthy = await textverified_client.health_check()
            response_time = time.time() - start_time
            
            status = ServiceStatus.HEALTHY if is_healthy else ServiceStatus.UNHEALTHY
            
            return HealthCheck(
                service="textverified",
                status=status,
                response_time=response_time,
                last_check=time.time(),
                error=None if is_healthy else "Health check failed"
            )
            
        except Exception as e:
            response_time = time.time() - start_time
            logger.error("TextVerified health check error: %s", e)
            
            return HealthCheck(
                service="textverified",
                status=ServiceStatus.UNHEALTHY,
                response_time=response_time,
                last_check=time.time(),
                error=str(e)
            )
    
    async def check_all_services(self) -> Dict[str, HealthCheck]:
        """Check health of all monitored services."""
        checks = {}
        
        # Check TextVerified
        textverified_check = await self.check_textverified_health()
        checks["textverified"] = textverified_check
        self.checks["textverified"] = textverified_check
        
        return checks
    
    async def get_system_health(self) -> Dict[str, Any]:
        """Get overall system health status."""
        checks = await self.check_all_services()
        
        healthy_count = sum(1 for check in checks.values() if check.status == ServiceStatus.HEALTHY)
        total_count = len(checks)
        
        if healthy_count == total_count:
            overall_status = ServiceStatus.HEALTHY
        elif healthy_count > 0:
            overall_status = ServiceStatus.DEGRADED
        else:
            overall_status = ServiceStatus.UNHEALTHY
            
        return {
            "status": overall_status.value,
            "timestamp": time.time(),
            "services": {
                name: {
                    "status": check.status.value,
                    "response_time": check.response_time,
                    "last_check": check.last_check,
                    "error": check.error
                }
                for name, check in checks.items()
            },
            "summary": {
                "healthy": healthy_count,
                "total": total_count,
                "uptime_percentage": (healthy_count / total_count) * 100 if total_count > 0 else 0
            }
        }
    
    async def start_monitoring(self):
        """Start continuous health monitoring."""
        self.running = True
        logger.info("Health monitoring started")
        
        while self.running:
            try:
                await self.check_all_services()
                await asyncio.sleep(self.check_interval)
            except Exception as e:
                logger.error("Health monitoring error: %s", e)
                await asyncio.sleep(self.check_interval)
    
    def stop_monitoring(self):
        """Stop health monitoring."""
        self.running = False
        logger.info("Health monitoring stopped")

# Global health monitor instance
health_monitor = HealthMonitor()