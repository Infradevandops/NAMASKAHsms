#!/usr/bin/env python3
"""
Minimal startup script that bypasses database connection issues during import.
This ensures the application starts even with database problems.
"""

import os
import sys
import logging
import uvicorn
from pathlib import Path

# Add the current directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

# Setup basic logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def setup_environment():
    """Setup environment variables for robust startup."""
    # Set fallback environment variables
    os.environ.setdefault("ALLOW_SQLITE_FALLBACK", "true")
    
    # Use SQLite fallback if no database URL is set
    if not os.getenv("DATABASE_URL"):
        os.environ["DATABASE_URL"] = "sqlite:///./namaskah_minimal.db"
        logger.info("🔄 No DATABASE_URL set, using SQLite fallback")
    
    # Set other defaults
    os.environ.setdefault("ENVIRONMENT", "production")
    os.environ.setdefault("DEBUG", "false")

def test_app_import():
    """Test if the app can be imported successfully."""
    try:
        logger.info("🧪 Testing application import...")
        from main import app
        logger.info("✅ Application imported successfully")
        return True
    except Exception as e:
        logger.error(f"❌ Application import failed: {e}")
        return False

def main():
    """Minimal startup function."""
    logger.info("=" * 60)
    logger.info("🚀 NAMASKAH SMS PLATFORM - MINIMAL STARTUP")
    logger.info("=" * 60)
    
    # Setup environment
    setup_environment()
    
    # Get configuration
    port = int(os.getenv("PORT", 8000))
    host = os.getenv("HOST", "0.0.0.0")
    
    logger.info(f"📊 Environment: {os.getenv('ENVIRONMENT', 'unknown')}")
    logger.info(f"🗄️  Database: {os.getenv('DATABASE_URL', 'unknown').split('@')[1] if '@' in os.getenv('DATABASE_URL', '') else os.getenv('DATABASE_URL', 'unknown')}")
    logger.info(f"🌐 Server: {host}:{port}")
    
    # Test app import
    if not test_app_import():
        logger.error("💥 Application import failed. Exiting.")
        sys.exit(1)
    
    logger.info("🎯 Starting server...")
    
    try:
        # Start the server directly
        uvicorn.run(
            "main:app",
            host=host,
            port=port,
            log_level="info",
            access_log=True,
            reload=False,
            workers=1
        )
        
    except Exception as e:
        logger.error(f"❌ Failed to start application: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
