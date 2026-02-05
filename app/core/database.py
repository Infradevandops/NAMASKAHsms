"""Database connection and session management."""

import os
import logging
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import QueuePool
from sqlalchemy.exc import OperationalError
from app.models.base import Base
from .config import settings

logger = logging.getLogger(__name__)

def create_database_engine():
    """Create database engine with fallback mechanism."""
    database_url = settings.database_url
    
    # Try to connect to the configured database
    if "sqlite" in database_url:
        # SQLite for development
        logger.info("Using SQLite database for development")
        return create_engine(database_url, connect_args={"check_same_thread": False})
    else:
        # PostgreSQL for production with fallback
        try:
            logger.info(f"Attempting to connect to PostgreSQL: {database_url.split('@')[1] if '@' in database_url else 'unknown'}")
            engine = create_engine(
                database_url,
                poolclass=QueuePool,
                pool_size=20,
                max_overflow=30,
                pool_pre_ping=True,
                pool_recycle=3600,
                echo=False,
            )
            
            logger.info("✅ PostgreSQL engine created (connection will be tested on first use)")
            return engine
            
        except Exception as e:
            logger.error(f"❌ PostgreSQL engine creation failed: {e}")
            
            # Check if we're in production and should fail hard
            if settings.environment == "production" and not os.getenv("ALLOW_SQLITE_FALLBACK"):
                logger.error("Production environment requires PostgreSQL. Set ALLOW_SQLITE_FALLBACK=true to use SQLite fallback.")
                raise
            
            # Fallback to SQLite
            fallback_db = "sqlite:///./namaskah_fallback.db"
            logger.warning(f"🔄 Falling back to SQLite: {fallback_db}")
            
            return create_engine(fallback_db, connect_args={"check_same_thread": False})

# Create engine with fallback (no connection test during import)
engine = create_database_engine()

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    """Dependency to get database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def create_tables():
    """Create all database tables."""
    try:
        # Import all models to ensure they're registered
        # Configure the registry to resolve relationships
        Base.registry.configure()
        Base.metadata.create_all(bind=engine)
        logger.info("✅ Database tables created successfully")
    except Exception as e:
        logger.error(f"❌ Failed to create database tables: {e}")
        raise


def drop_tables():
    """Drop all database tables."""
    Base.metadata.drop_all(bind=engine)


def test_database_connection():
    """Test database connection and return status."""
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return {"status": "connected", "engine": str(engine.url).split('@')[0] + '@***'}
    except Exception as e:
        return {"status": "failed", "error": str(e)}


def ensure_database_connection():
    """Ensure database connection is working, with fallback if needed."""
    global engine, SessionLocal
    
    try:
        # Test the current engine
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        logger.info("✅ Database connection verified")
        return True
    except Exception as e:
        logger.error(f"❌ Database connection failed: {e}")
        
        # If we're using PostgreSQL and fallback is allowed, switch to SQLite
        if "postgresql" in str(engine.url) and os.getenv("ALLOW_SQLITE_FALLBACK"):
            logger.warning("🔄 Switching to SQLite fallback")
            
            fallback_db = "sqlite:///./namaskah_fallback.db"
            engine = create_engine(fallback_db, connect_args={"check_same_thread": False})
            SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
            
            try:
                with engine.connect() as conn:
                    conn.execute(text("SELECT 1"))
                logger.info("✅ SQLite fallback connection successful")
                return True
            except Exception as fallback_error:
                logger.error(f"❌ SQLite fallback also failed: {fallback_error}")
                return False
        
        return False