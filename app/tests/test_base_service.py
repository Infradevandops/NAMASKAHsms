"""Tests for base service infrastructure."""
import pytest
from sqlalchemy import Column, String, create_engine
from sqlalchemy.orm import sessionmaker

from app.models.base import Base, BaseModel
from app.services.base import BaseService, get_service


class TestServiceModel(BaseModel):
    """Test model for service testing."""
    __tablename__ = "test_service_models"

    name = Column(String, nullable=False)
    description = Column(String)


@pytest.fixture
def db_session():
    """Create test database session."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    return Session()


@pytest.fixture
def service(db_session):
    """Create test service instance."""
    return BaseService(TestServiceModel, db_session)


def test_service_create(service):
    """Test service create operation."""
    instance = service.create(name="Test Item", description="Test Description")

    assert instance is not None
    assert instance.name == "Test Item"
    assert instance.description == "Test Description"
    assert instance.id is not None


def test_service_get_by_id(service):
    """Test service get by ID operation."""
    # Create instance
    created = service.create(name="Test Item")

    # Get by ID
    retrieved = service.get_by_id(created.id)

    assert retrieved is not None
    assert retrieved.id == created.id
    assert retrieved.name == "Test Item"


def test_service_get_by_id_not_found(service):
    """Test service get by ID when not found."""
    result = service.get_by_id("nonexistent_id")
    assert result is None


def test_service_get_all(service):
    """Test service get all operation."""
    # Create multiple instances
    service.create(name="Item 1")
    service.create(name="Item 2")
    service.create(name="Item 3")

    # Get all
    all_items = service.get_all()

    assert len(all_items) == 3
    assert all([item.name.startswith("Item") for item in all_items])


def test_service_get_all_with_pagination(service):
    """Test service get all with pagination."""
    # Create multiple instances
    for i in range(5):
        service.create(name=f"Item {i}")

    # Get with pagination
    page1 = service.get_all(limit=2, offset=0)
    page2 = service.get_all(limit=2, offset=2)

    assert len(page1) == 2
    assert len(page2) == 2
    assert page1[0].id != page2[0].id


def test_service_update(service):
    """Test service update operation."""
    # Create instance
    created = service.create(name="Original Name")

    # Update
    updated = service.update(created.id, name="Updated Name", description="New Description")

    assert updated is not None
    assert updated.id == created.id
    assert updated.name == "Updated Name"
    assert updated.description == "New Description"
    assert updated.updated_at is not None


def test_service_update_not_found(service):
    """Test service update when instance not found."""
    result = service.update("nonexistent_id", name="New Name")
    assert result is None


def test_service_delete(service):
    """Test service delete operation."""
    # Create instance
    created = service.create(name="To Delete")

    # Delete
    success = service.delete(created.id)

    assert success is True

    # Verify deletion
    retrieved = service.get_by_id(created.id)
    assert retrieved is None


def test_service_delete_not_found(service):
    """Test service delete when instance not found."""
    success = service.delete("nonexistent_id")
    assert success is False


def test_service_count(service):
    """Test service count operation."""
    # Initially empty
    assert service.count() == 0

    # Create instances
    service.create(name="Item 1")
    service.create(name="Item 2")

    # Check count
    assert service.count() == 2


def test_service_factory(db_session):
    """Test service factory function."""
    service = get_service(TestServiceModel, db_session)

    assert isinstance(service, BaseService)
    assert service.model == TestServiceModel
    assert service.db == db_session


if __name__ == "__main__":
    pytest.main([__file__])
