"""Application lifespan management - Minimal version for CI fix."""

import asyncio
import os
from contextlib import asynccontextmanager

from app.core.database import engine
from app.core.init_admin import init_admin_user
from app.core.logging import get_logger
from app.models.base import Base

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

        try:
            await asyncio.wait_for(cache.connect(), timeout=10.0)
            startup_logger.info("Unified cache initialized")
        except asyncio.TimeoutError:
            startup_logger.warning(
                "Cache connection timeout - continuing without cache"
            )
        except Exception as e:
            startup_logger.warning(f"Cache initialization failed: {e}")

        # Invalidate stale service cache (forces fresh fetch with dedup + real prices)
        try:
            from app.core.unified_cache import cache as _cache

            await _cache.delete("tv:services_list")
            await _cache.delete("tv:services_names")
            startup_logger.info("Cleared stale service cache")
        except Exception as e:
            startup_logger.warning(f"Cache clear failed (non-critical): {e}")

        # Pre-warm services and area codes cache (non-blocking background task)
        async def _prewarm():
            try:
                from app.services.textverified_service import TextVerifiedService

                tv = TextVerifiedService()
                if not tv.enabled:
                    startup_logger.error(
                        "⚠️  TextVerified is DISABLED — SMS verification will not work. "
                        "Set TEXTVERIFIED_API_KEY and TEXTVERIFIED_EMAIL in your environment."
                    )
                    return

                # Skip area codes prewarm if already cached (but services always re-fetch)
                startup_logger.info("Pre-warming TextVerified cache...")
                await asyncio.wait_for(
                    asyncio.gather(
                        tv.get_services_list(),
                        tv.get_area_codes_list(),
                        return_exceptions=True,
                    ),
                    timeout=15.0,
                )
                startup_logger.info("Cache pre-warming completed")
            except asyncio.TimeoutError:
                startup_logger.warning(
                    "Cache pre-warming timed out (will retry on next request)"
                )
            except Exception as e:
                startup_logger.warning(f"Cache pre-warming failed (non-critical): {e}")

        # Skip pre-warming in test mode
        if os.getenv("TESTING") != "1":
            asyncio.create_task(_prewarm())
        else:
            startup_logger.info("Skipping TextVerified pre-warming in test mode")

        # Start SMS polling background service
        if os.getenv("TESTING") != "1":
            from app.services.refund_policy_enforcer import refund_policy_enforcer
            from app.services.sms_polling_service import sms_polling_service

            polling_task = asyncio.create_task(
                sms_polling_service.start_background_service()
            )
            startup_logger.info("✅ SMS polling background service started")

            # Start refund policy enforcer (backup to polling service)
            enforcer_task = asyncio.create_task(
                refund_policy_enforcer.start_enforcement()
            )
            startup_logger.info("✅ Refund policy enforcer started (5-min backup)")

            # Start institutional health audit loop (V6.0 Mastery)
            from app.services.providers.provider_health_check import (
                start_health_audit_loop,
            )

            asyncio.create_task(start_health_audit_loop())
            startup_logger.info(
                "✅ Institutional health audit loop started (every 4 hours)"
            )

            # Start rental expiry monitor (V6.0)
            from app.services.rental_service import start_rental_expiry_monitor

            asyncio.create_task(start_rental_expiry_monitor())
            startup_logger.info("✅ Rental expiry monitor started (every 30 minutes)")

            # Start daily growth snapshot loop (Institutional Mastery)
            async def start_daily_snapshot_loop():
                while True:
                    try:
                        from app.core.database import SessionLocal
                        from app.services.target_tracking_service import TargetTrackingService
                        
                        async with SessionLocal() as db:
                            service = TargetTrackingService(db)
                            snapshot = await service.record_daily_snapshot()
                            if snapshot:
                                startup_logger.info(f"✅ Midnight growth snapshot recorded for {snapshot.snapshot_date}")
                    except Exception as e:
                        startup_logger.error(f"❌ Daily snapshot failed: {e}")
                    
                    # Sleep until next midnight (approx 24h)
                    await asyncio.sleep(86400)

            asyncio.create_task(start_daily_snapshot_loop())
            startup_logger.info("✅ Daily growth snapshotting active (24h loop)")
        else:
            startup_logger.info("Skipping SMS polling in test mode")

    except Exception as e:
        startup_logger.error(f"Startup failed: {e}")
        raise

    # Application is running
    yield

    # Shutdown
    startup_logger.info("🛑 Shutting down Namaskah SMS API...")
    if os.getenv("TESTING") != "1":
        from app.services.refund_policy_enforcer import refund_policy_enforcer
        from app.services.sms_polling_service import sms_polling_service

        await sms_polling_service.stop_background_service()
        await refund_policy_enforcer.stop_enforcement()
        startup_logger.info("✅ Background services stopped")
    from app.core.unified_cache import cache

    try:
        await cache.disconnect()
    except Exception as e:
        startup_logger.warning(f"Cache disconnect failed: {e}")
    startup_logger.info("✅ Shutdown completed")
