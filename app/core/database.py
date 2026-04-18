"""Database connection and session management with resilience patterns."""

import logging
import os
import time
from typing import Optional

from sqlalchemy import create_engine, text
from sqlalchemy.exc import DisconnectionError, OperationalError
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import QueuePool

from app.models.base import Base

from .config import settings

logger = logging.getLogger(__name__)


class DatabaseConnectionManager:
    """Manages database connections with retry logic and circuit breaker."""

    def __init__(self):
        self.engine = None
        self.SessionLocal = None
        self.circuit_breaker_failures = 0
        self.circuit_breaker_last_failure = 0
        self.circuit_breaker_threshold = 5
        self.circuit_breaker_timeout = 60  # seconds
        self.max_retries = 3
        self.retry_delays = [1, 2, 4]  # exponential backoff

    def is_circuit_breaker_open(self) -> bool:
        """Check if circuit breaker is open."""
        if self.circuit_breaker_failures < self.circuit_breaker_threshold:
            return False

        time_since_failure = time.time() - self.circuit_breaker_last_failure
        if time_since_failure > self.circuit_breaker_timeout:
            # Reset circuit breaker
            self.circuit_breaker_failures = 0
            return False

        return True

    def record_failure(self):
        """Record a connection failure."""
        self.circuit_breaker_failures += 1
        self.circuit_breaker_last_failure = time.time()
        logger.warning(
            f"Database failure recorded. Count: {self.circuit_breaker_failures}"
        )

    def record_success(self):
        """Record a successful connection."""
        if self.circuit_breaker_failures > 0:
            logger.info("Database connection recovered. Resetting circuit breaker.")
        self.circuit_breaker_failures = 0

    def create_engine_with_retry(self) -> Optional[object]:
        """Create database engine with retry logic."""
        database_url = settings.database_url

        for attempt in range(self.max_retries):
            try:
                if "sqlite" in database_url:
                    engine = create_engine(
                        database_url, connect_args={"check_same_thread": False}
                    )
                else:
                    engine = create_engine(
                        database_url,
                        poolclass=QueuePool,
                        pool_size=10,
                        max_overflow=20,
                        pool_pre_ping=True,
                        pool_recycle=3600,
                        echo=False,
                        connect_args={
                            "connect_timeout": 10,
                            "application_name": "namaskah_sms",
                        },
                    )

                # Test connection
                with engine.connect() as conn:
                    conn.execute(text("SELECT 1"))

                logger.info(
                    f"Database engine created successfully on attempt {attempt + 1}"
                )
                self.record_success()
                return engine

            except Exception as e:
                logger.error(f"Database connection attempt {attempt + 1} failed: {e}")

                if attempt < self.max_retries - 1:
                    delay = self.retry_delays[attempt]
                    logger.info(f"Retrying in {delay} seconds...")
                    time.sleep(delay)
                else:
                    self.record_failure()

        return None

    def initialize(self):
        """Initialize database connection with fallback."""
        if os.getenv("USE_TEST_DB") == "true":
            logger.info("USE_TEST_DB is true, jumping to fallback SQLite")
            return self._create_fallback_engine()

        if self.is_circuit_breaker_open():
            logger.warning("Circuit breaker is open. Using fallback connection.")
            return self._create_fallback_engine()

        engine = self.create_engine_with_retry()

        if engine is None:
            logger.error("All connection attempts failed. Using fallback.")
            return self._create_fallback_engine()

        self.engine = engine
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        return True

    def _create_fallback_engine(self):
        """Create SQLite fallback engine."""
        if settings.environment == "production" and not os.getenv(
            "ALLOW_SQLITE_FALLBACK"
        ):
            logger.error(
                "Production requires PostgreSQL. Set ALLOW_SQLITE_FALLBACK=true for fallback."
            )
            raise RuntimeError("Database connection failed and fallback not allowed")

        fallback_db = "sqlite:///./namaskah_fallback.db"
        logger.warning(f"Using SQLite fallback: {fallback_db}")

        try:
            self.engine = create_engine(
                fallback_db, connect_args={"check_same_thread": False}
            )
            self.SessionLocal = sessionmaker(
                autocommit=False, autoflush=False, bind=self.engine
            )

            # Test fallback connection
            with self.engine.connect() as conn:
                conn.execute(text("SELECT 1"))

            logger.info("SQLite fallback connection successful")
            return True

        except Exception as e:
            logger.error(f"SQLite fallback failed: {e}")
            raise RuntimeError("Both primary and fallback database connections failed")

    def get_session(self):
        """Get database session with connection validation."""
        if not self.engine or not self.SessionLocal:
            self.initialize()

        session = self.SessionLocal()

        try:
            # Validate connection
            session.execute(text("SELECT 1"))
            return session
        except (OperationalError, DisconnectionError) as e:
            logger.error(f"Session validation failed: {e}")
            session.close()

            # Try to reinitialize
            if self.initialize():
                return self.SessionLocal()
            else:
                raise RuntimeError("Database session creation failed")


# Global connection manager
db_manager = DatabaseConnectionManager()


def get_session_local():
    """Returns the SessionLocal class, initializing if needed."""
    if not db_manager.SessionLocal:
        db_manager.initialize()
    return db_manager.SessionLocal


def get_engine():
    """Returns the engine, initializing if needed."""
    if not db_manager.engine:
        db_manager.initialize()
    return db_manager.engine


# Legacy compatibility wrapper
class SessionLocalWrapper:
    def __call__(self, *args, **kwargs):
        return get_session_local()(*args, **kwargs)

    def __getattr__(self, name):
        return getattr(get_session_local(), name)


class EngineWrapper:
    def __getattr__(self, name):
        return getattr(get_engine(), name)

    def __str__(self):
        return str(get_engine())

    def __repr__(self):
        return repr(get_engine())


SessionLocal = SessionLocalWrapper()
engine = EngineWrapper()


def get_db():
    """Dependency to get database session with resilience."""
    from fastapi import HTTPException

    session = None
    try:
        session = db_manager.get_session()
        yield session
    except HTTPException:
        # Business logic exceptions — let them propagate without DB error logging
        if session:
            session.rollback()
        raise
    except (OperationalError, DisconnectionError, RuntimeError) as e:
        logger.error(f"Database session error: {e}")
        if session:
            session.rollback()
        raise
    except Exception as e:
        logger.error(f"Database session error: {e}")
        if session:
            session.rollback()
        raise
    finally:
        if session:
            session.close()


def create_tables():
    """Create all database tables with retry logic."""
    if not db_manager.engine:
        db_manager.initialize()
        
    max_retries = 3
    for attempt in range(max_retries):
        try:
            Base.registry.configure()
            Base.metadata.create_all(bind=db_manager.engine)
            logger.info("Database tables created successfully")
            return
        except Exception as e:
            logger.error(f"Failed to create tables (attempt {attempt + 1}): {e}")
            if attempt < max_retries - 1:
                time.sleep(2**attempt)  # exponential backoff
            else:
                raise


def drop_tables():
    """Drop all database tables."""
    try:
        Base.metadata.drop_all(bind=db_manager.engine)
        logger.info("Database tables dropped successfully")
    except Exception as e:
        logger.error(f"Failed to drop tables: {e}")
        raise


def test_database_connection():
    """Test database connection and return detailed status."""
    try:
        with db_manager.engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return {
            "status": "connected",
            "engine": str(db_manager.engine.url).split("@")[0] + "@***",
            "circuit_breaker_failures": db_manager.circuit_breaker_failures,
            "circuit_breaker_open": db_manager.is_circuit_breaker_open(),
        }
    except Exception as e:
        return {
            "status": "failed",
            "error": str(e),
            "circuit_breaker_failures": db_manager.circuit_breaker_failures,
            "circuit_breaker_open": db_manager.is_circuit_breaker_open(),
        }
