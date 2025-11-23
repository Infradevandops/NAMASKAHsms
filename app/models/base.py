"""Base model infrastructure with common fields and patterns."""
from datetime import datetime, timezone
import uuid

from sqlalchemy import Column, DateTime, String, Boolean

Base = declarative_base()


class BaseModel(Base):
    """Base model class with common fields for all models."""

    __abstract__ = True

    id = Column(String, primary_key=True)
    created_at = Column(
        DateTime, default=lambda: datetime.now(timezone.utc), nullable=False
    )
    updated_at = Column(DateTime, onupdate=lambda: datetime.now(timezone.utc))
    # deleted_at = Column(DateTime, nullable=True)
    # is_deleted = Column(Boolean, default=False, nullable=False)

    def __init__(self, **kwargs):
        if "id" not in kwargs:
            kwargs["id"] = str(uuid.uuid4())
        super().__init__(**kwargs)

    def to_dict(self):
        """Convert model instance to dictionary."""
        return {
            column.name: getattr(self, column.name) for column in self.__table__.columns
        }

    def update_timestamp(self):
        """Update the updated_at timestamp."""
        self.updated_at = datetime.now(timezone.utc)

    # def soft_delete(self):
    #     """Mark record as deleted without removing from database."""
    #     self.is_deleted = True
    #     self.deleted_at = datetime.now(timezone.utc)
    #     self.update_timestamp()
    #
    # def restore(self):
    #     """Restore soft-deleted record."""
    #     self.is_deleted = False
    #     self.deleted_at = None
    #     self.update_timestamp()
