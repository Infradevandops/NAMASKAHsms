"""Tests for base model infrastructure."""
from datetime import datetime, timezone

import pytest
from sqlalchemy import Column, String, create_engine
from sqlalchemy.orm import sessionmaker

from app.models.base import Base, BaseModel


class TestModel(BaseModel):
    """Test model for base model functionality."""
    __tablename__ = "test_models"

    name = Column(String, nullable=False)


@pytest.fixture
def db_session():
    """Create test database session."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    return Session()


def test_base_model_id_generation():
    """Test automatic ID generation."""
    model = TestModel(name="test")

    assert model.id is not None
    assert model.id.startswith("test_model_")
    assert len(model.id) > 15


def test_base_model_timestamps():
    """Test automatic timestamp creation."""
    model = TestModel(name="test")

    assert model.created_at is not None
    assert isinstance(model.created_at, datetime)
    assert model.updated_at is None  # Only set on update


def test_base_model_to_dict():
    """Test model to dictionary conversion."""
    model = TestModel(name="test")

    data = model.to_dict()

    assert isinstance(data, dict)
    assert "id" in data
    assert "name" in data
    assert "created_at" in data
    assert data["name"] == "test"


def test_base_model_update_timestamp():
    """Test manual timestamp update."""
    model = TestModel(name="test")
    original_created = model.created_at

    model.update_timestamp()

    assert model.updated_at is not None
    assert model.updated_at > original_created


def test_base_model_custom_id():
    """Test custom ID override."""
    custom_id = "custom_123"
    model = TestModel(id=custom_id, name="test")

    assert model.id == custom_id


def test_base_model_database_operations(db_session):
    """Test database operations with base model."""
    model = TestModel(name="test")

    # Add to database
    db_session.add(model)
    db_session.commit()

    # Query back
    retrieved = db_session.query(TestModel).filter(TestModel.name == "test").first()

    assert retrieved is not None
    assert retrieved.id == model.id
    assert retrieved.name == "test"
    assert retrieved.created_at is not None


if __name__ == "__main__":
    pytest.main([__file__])
