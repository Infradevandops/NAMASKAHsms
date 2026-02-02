"""Base service infrastructure with generic CRUD operations."""

from typing import Generic, List, Optional, Type, TypeVar
from sqlalchemy.orm import Session
from app.models.base import BaseModel

T = TypeVar("T", bound=BaseModel)


class BaseService(Generic[T]):
    """Base service class with generic CRUD operations."""

    def __init__(self, model: Type[T], db: Session):
        self.model = model
        self.db = db

    def create(self, **kwargs) -> T:
        """Create a new model instance."""
        instance = self.model(**kwargs)
        self.db.add(instance)
        self.db.commit()
        self.db.refresh(instance)
        return instance

    def get_by_id(self, id: str) -> Optional[T]:
        """Get model instance by ID."""
        return self.db.query(self.model).filter(self.model.id == id).first()

    def get_all(self, limit: int = 100, offset: int = 0) -> List[T]:
        """Get all model instances with pagination."""
        return self.db.query(self.model).offset(offset).limit(limit).all()

    def update(self, id: str, **kwargs) -> Optional[T]:
        """Update model instance by ID."""
        instance = self.get_by_id(id)
        if not instance:
            return None

        for key, value in kwargs.items():
            if hasattr(instance, key):
                setattr(instance, key, value)

        instance.update_timestamp()
        self.db.commit()
        self.db.refresh(instance)
        return instance

    def delete(self, id: str) -> bool:
        """Delete model instance by ID."""
        instance = self.get_by_id(id)
        if not instance:
            return False

        self.db.delete(instance)
        self.db.commit()
        return True

    def count(self) -> int:
        """Get total count of model instances."""
        return self.db.query(self.model).count()


def get_service(model: Type[T], db: Session) -> BaseService[T]:
    """Service factory function."""
    return BaseService(model, db)