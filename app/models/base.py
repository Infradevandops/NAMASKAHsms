"""Base model infrastructure with common fields and patterns."""
from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, String
from sqlalchemy.orm import declarative_base

from app.utils.security import generate_secure_id

Base = declarative_base()


class BaseModel(Base):
    """Base model class with common fields for all models."""

    __abstract__ = True

    id = Column(String, primary_key=True)
    created_at = Column(
        DateTime, default=lambda: datetime.now(timezone.utc), nullable=False
    )
    updated_at = Column(DateTime, onupdate=lambda: datetime.now(timezone.utc))

    def __init__(self, **kwargs):
        if "id" not in kwargs:
            # Generate ID with table name prefix
            table_name = self.__tablename__
            prefix = table_name.rstrip("s")  # Remove trailing 's'
            kwargs["id"] = generate_secure_id(prefix)
        super().__init__(**kwargs)

    def to_dict(self):
        """Convert model instance to dictionary."""
        return {
            column.name: getattr(self, column.name) for column in self.__table__.columns
        }

    def update_timestamp(self):
        """Update the updated_at timestamp."""
        self.updated_at = datetime.now(timezone.utc)
