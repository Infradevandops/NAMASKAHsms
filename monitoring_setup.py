"""Production monitoring and health check setup."""
import asyncio
from datetime import datetime
from app.core.logging import get_logger
from app.services.textverified_integration import get_textverified_integration

logger = get_logger(__name__)


class HealthMonitor:
    """Monitor system health and API connectivity."""

    def __init__(self):
        self.integration = get_textverified_integration()
        self.last_check = None
        self.status = "healthy"

    async def check_textverified_api(self) -> bool:
        """Check TextVerified API connectivity."""
        try:
            balance = await self.integration.get_account_balance(force_refresh=True)
            logger.info(f"TextVerified API OK - Balance: ${balance}")
            return True
        except Exception as e:
            logger.error(f"TextVerified API Error: {e}")
            return False

    async def check_database(self, db) -> bool:
        """Check database connectivity."""
        try:
            db.execute("SELECT 1")
            logger.info("Database OK")
            return True
        except Exception as e:
            logger.error(f"Database Error: {e}")
            return False

    async def check_cache(self) -> bool:
        """Check cache connectivity."""
        try:
            from app.core.cache_manager import cache_manager
            await cache_manager.set("health_check", "ok", ttl=60)
            value = await cache_manager.get("health_check")
            if value == "ok":
                logger.info("Cache OK")
                return True
        except Exception as e:
            logger.warning(f"Cache Error (non-critical): {e}")
            return True  # Cache is optional

    async def run_health_check(self, db) -> dict:
        """Run full health check."""
        results = {
            "timestamp": datetime.utcnow().isoformat(),
            "textverified_api": await self.check_textverified_api(),
            "database": await self.check_database(db),
            "cache": await self.check_cache(),
        }

        all_ok = all(results.values())
        results["status"] = "healthy" if all_ok else "degraded"
        self.status = results["status"]
        self.last_check = datetime.utcnow()

        logger.info(f"Health check: {results['status']}")
        return results


async def start_monitoring():
    """Start background monitoring."""
    monitor = HealthMonitor()

    async def monitor_loop():
        while True:
            try:
                from app.core.database import SessionLocal
                db = SessionLocal()
                await monitor.run_health_check(db)
                db.close()
                await asyncio.sleep(300)  # Check every 5 minutes
            except Exception as e:
                logger.error(f"Monitoring error: {e}")
                await asyncio.sleep(60)

    return asyncio.create_task(monitor_loop())
