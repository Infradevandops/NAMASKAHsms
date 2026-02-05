#!/usr/bin/env python3
"""
Robust startup script with database fallback mechanism.
This script ensures the application starts even if the primary database is unavailable.
"""

import os
import sys
import logging
import uvicorn
from pathlib import Path

# Add the current directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def check_environment():
    """Check and log environment configuration."""
    env = os.getenv("ENVIRONMENT", "development")
    db_url = os.getenv("DATABASE_URL", "sqlite:///./namaskah.db")
    
    logger.info(f"🚀 Starting Namaskah SMS Platform")
    logger.info(f"📊 Environment: {env}")
    logger.info(f"🗄️  Database: {db_url.split('@')[1] if '@' in db_url else db_url}")
    
    # Check for fallback option
    if os.getenv("ALLOW_SQLITE_FALLBACK"):
        logger.info("🔄 SQLite fallback enabled")
    
    return env

def test_database_connection():
    """Test database connection before starting the app."""
    try:
        from app.core.database import ensure_database_connection
        
        if ensure_database_connection():
            logger.info("✅ Database connection verified")
            return True
        else:
            logger.error("❌ Database connection failed")
            return False
            
    except Exception as e:
        logger.error(f"❌ Database test failed: {e}")
        return False

def create_tables_if_needed():
    """Create database tables if they don't exist."""
    try:
        from app.core.database import create_tables
        create_tables()
        logger.info("✅ Database tables ready")
        return True
    except Exception as e:
        logger.error(f"❌ Failed to create tables: {e}")
        return False

def start_application():
    """Start the FastAPI application."""
    try:
        # Import the app
        from main import app
        
        # Get configuration
        port = int(os.getenv("PORT", 9527))
        host = os.getenv("HOST", "0.0.0.0")
        
        logger.info(f"🌐 Starting server on {host}:{port}")
        
        # Start the server
        uvicorn.run(
            app,
            host=host,
            port=port,
            log_level="info",
            access_log=True
        )
        
    except Exception as e:
        logger.error(f"❌ Failed to start application: {e}")
        sys.exit(1)

def main():
    """Main startup function."""
    logger.info("=" * 60)
    logger.info("🚀 NAMASKAH SMS PLATFORM STARTUP")
    logger.info("=" * 60)
    
    # Check environment
    env = check_environment()
    
    # Test database connection
    if not test_database_connection():
        if env == "production" and not os.getenv("ALLOW_SQLITE_FALLBACK"):
            logger.error("💥 Production requires database connection. Exiting.")
            sys.exit(1)
        else:
            logger.warning("⚠️  Database connection failed, but continuing with fallback")
    
    # Create tables
    if not create_tables_if_needed():
        logger.error("💥 Failed to initialize database. Exiting.")
        sys.exit(1)
    
    # Start application
    logger.info("🎯 All checks passed. Starting application...")
    start_application()

if __name__ == "__main__":
    main()
