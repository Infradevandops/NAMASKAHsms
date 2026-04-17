"""Test Pydantic compatibility layer."""

import pytest

from app.core.pydantic_compat import PYDANTIC_V2, BaseModel, field_validator


class TestModel(BaseModel):
    """Test model for compatibility testing."""

    email: str
    age: int

    @field_validator("email", mode="before")
    @classmethod
    def validate_email(cls, v):
        if "@" not in str(v):
            raise ValueError("Invalid email")
        return v

    @field_validator("age")
    @classmethod
    def validate_age(cls, v):
        if v < 0:
            raise ValueError("Age must be positive")
        return v


def test_pydantic_compatibility():
    model = TestModel(email="test@example.com", age=25)
    assert model.email == "test@example.com"
    assert model.age == 25

    with pytest.raises(ValueError, match="Invalid email"):
        TestModel(email="invalid-email", age=25)

    with pytest.raises(ValueError, match="Age must be positive"):
        TestModel(email="test@example.com", age=-1)


def test_pydantic_version_detection():
    assert isinstance(PYDANTIC_V2, bool)
    assert PYDANTIC_V2 is True
