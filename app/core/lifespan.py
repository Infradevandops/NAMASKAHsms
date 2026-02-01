"""Application lifespan management."""


import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.core.config import get_settings
from app.core.database import engine
from app.core.logging import get_logger
from app.core.startup import run_startup_initialization
from app.core.unified_cache import cache
from app.models.base import Base
import os
from app.services.sms_polling_service import sms_polling_service
from app.services.voice_polling_service import voice_polling_service

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan context manager - handles startup and shutdown."""
    startup_logger = get_logger("startup")
    settings = get_settings()

    # ============== STARTUP ==============
    startup_logger.info("Application startup - Phase 1")

    # Connect to cache
try:
        startup_logger.info("Connecting to cache...")
        await cache.connect()
        startup_logger.info("Cache connected successfully")
except Exception as e:
        startup_logger.error(f"Cache connection error: {e}")
        startup_logger.warning("Continuing with in-memory cache fallback")

    # Initialize database
try:
        startup_logger.info("Initializing database...")

        Base.registry.configure()
        Base.metadata.create_all(bind=engine)
        startup_logger.info("Database tables created successfully")
except Exception as e:
        startup_logger.error(f"Database initialization error: {e}")
        raise

    # Create admin user if needed
try:
        startup_logger.info("Checking admin user...")

if os.getenv("TESTING") != "1":
            run_startup_initialization()

        startup_logger.info("Admin user verified")
except Exception as e:
        startup_logger.error(f"Admin user initialization error: {e}")

    # Start background services

    sms_task = None
    voice_task = None

    async def _run_sms_service_supervisor():
        sms_logger = get_logger("sms-supervisor")
while True:
try:
                await asyncio.wait_for(
                    sms_polling_service.start_background_service(),
                    timeout=settings.async_task_timeout_seconds,
                )
                sms_logger.info("SMS polling service exited; restarting supervisor in 5s")
                await asyncio.sleep(5)
except asyncio.TimeoutError:
                sms_logger.warning("SMS polling service timed out; restarting")
                await asyncio.sleep(2)
except asyncio.CancelledError:
                sms_logger.info("SMS supervisor cancelled")
                break
except Exception as e:
                sms_logger.error(f"SMS supervisor error: {e}")
                await asyncio.sleep(5)

    async def _run_voice_service_supervisor():
        voice_logger = get_logger("voice-supervisor")
while True:
try:
                await asyncio.wait_for(
                    voice_polling_service.start_background_service(),
                    timeout=settings.async_task_timeout_seconds,
                )
                voice_logger.info("Voice polling service exited; restarting supervisor in 5s")
                await asyncio.sleep(5)
except asyncio.TimeoutError:
                voice_logger.warning("Voice polling service timed out; restarting")
                await asyncio.sleep(2)
except asyncio.CancelledError:
                voice_logger.info("Voice supervisor cancelled")
                break
except Exception as e:
                voice_logger.error(f"Voice supervisor error: {e}")
                await asyncio.sleep(5)

    sms_task = asyncio.create_task(_run_sms_service_supervisor())
    voice_task = asyncio.create_task(_run_voice_service_supervisor())

    startup_logger.info("Application startup completed successfully")

    # ============== YIELD (app runs) ==============
    yield

    # ============== SHUTDOWN ==============
    shutdown_logger = get_logger("shutdown")
    shutdown_logger.info("Starting graceful shutdown")

try:
        # Cancel background tasks
if sms_task:
            sms_task.cancel()
if voice_task:
            voice_task.cancel()

        # Stop polling services
        await sms_polling_service.stop_background_service()
        await voice_polling_service.stop_background_service()
        shutdown_logger.info("Polling services stopped")

        # Disconnect cache
        await cache.disconnect()
        shutdown_logger.info("Cache disconnected")

        # Dispose database connections
        engine.dispose()
        shutdown_logger.info("Database connections disposed")

        shutdown_logger.info("Graceful shutdown completed")
except Exception as e:
        shutdown_logger.error(f"Error during shutdown: {e}")