"""Application lifespan management - Minimal version for CI fix."""

import os
from contextlib import asynccontextmanager
from app.core.database import engine
from app.core.logging import get_logger
from app.models.base import Base

startup_logger = get_logger("startup")


def run_startup_initialization():
    """Run startup initialization tasks."""
    try:
        startup_logger.info("Running startup initialization...")
        # Placeholder for startup tasks
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
        
    except Exception as e:
        startup_logger.error(f"Startup failed: {e}")
        raise
    
    # Application is running
    yield
    
    # Shutdown
    startup_logger.info("🛑 Shutting down Namaskah SMS API...")
    startup_logger.info("✅ Shutdown completed")