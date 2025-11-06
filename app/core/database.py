"""Database connection and session management."""

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import QueuePool

from .config import settings

# Database engine with connection pooling
if "sqlite" in settings.database_url:
    # SQLite for development only
    engine = create_engine(
        settings.database_url, connect_args={"check_same_thread": False}
    )
else:
    # PostgreSQL for production
    engine = create_engine(
        settings.database_url,
        poolclass=QueuePool,
        pool_size=20,  # Production pool size
        max_overflow=30,  # Max overflow connections
        pool_pre_ping=True,
        pool_recycle=3600,
        echo=False,  # Disable SQL logging in production
    )

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for models
Base = declarative_base()


def get_db():
    """Dependency to get database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def create_tables():
    """Create all database tables."""
    Base.metadata.create_all(bind=engine)


def drop_tables():
    """Drop all database tables."""
    Base.metadata.drop_all(bind=engine)
