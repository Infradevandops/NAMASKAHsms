"""Application lifespan management - Minimal version for CI fix."""

import os
import asyncio
from contextlib import asynccontextmanager
from app.core.database import engine
from app.core.logging import get_logger
from app.models.base import Base
from app.core.init_admin import init_admin_user

startup_logger = get_logger("startup")


def run_startup_initialization():
    """Run startup initialization tasks."""
    try:
        startup_logger.info("Running startup initialization...")
        init_admin_user()
        startup_logger.info("Startup initialization completed")
    except Exception as e:
        startup_logger.error(f"Startup initialization failed: {e}")


@asynccontextmanager
async def lifespan(app):
    """Application lifespan manager."""
    startup_logger.info("🚀 Starting Namaskah SMS API...")

    try:
        # Initialize database
        startup_logger.info("Initializing database...")
        Base.registry.configure()
        Base.metadata.create_all(bind=engine)
        startup_logger.info("Database tables created successfully")

        # Create admin user if needed
        startup_logger.info("Checking admin user...")
        if os.getenv("TESTING") != "1":
            run_startup_initialization()
        startup_logger.info("Admin user verified")

        startup_logger.info("✅ Application startup completed successfully")

        # Initialize unified cache
        from app.core.unified_cache import cache
        await cache.connect()
        startup_logger.info("Unified cache initialized")

        # Pre-warm services and area codes cache
        try:
            from app.services.textverified_service import TextVerifiedService
            tv = TextVerifiedService()
            if tv.enabled:
                startup_logger.info("Pre-warming TextVerified cache...")
                services_task = asyncio.create_task(tv.get_services_list())
                area_codes_task = asyncio.create_task(tv.get_area_codes_list())
                # Wait for completion with timeout
                try:
                    await asyncio.wait_for(asyncio.gather(services_task, area_codes_task, return_exceptions=True), timeout=30.0)
                    startup_logger.info("Cache pre-warming completed")
                except asyncio.TimeoutError:
                    startup_logger.warning("Cache pre-warming timed out (will retry in background)")
        except Exception as e:
            startup_logger.warning(f"Cache pre-warming failed (non-critical): {e}")

        # Start SMS polling background service
        from app.services.sms_polling_service import sms_polling_service
        polling_task = asyncio.create_task(sms_polling_service.start_background_service())
        startup_logger.info("SMS polling background service started")

    except Exception as e:
        startup_logger.error(f"Startup failed: {e}")
        raise

    # Application is running
    yield

    # Shutdown
    startup_logger.info("🛑 Shutting down Namaskah SMS API...")
    from app.services.sms_polling_service import sms_polling_service
    await sms_polling_service.stop_background_service()
    from app.core.unified_cache import cache
    await cache.disconnect()
    startup_logger.info("✅ Shutdown completed")