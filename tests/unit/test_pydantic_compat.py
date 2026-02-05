"""Test Pydantic compatibility layer."""


import pytest
from app.core.pydantic_compat import field_validator, BaseModel, PYDANTIC_V2

class TestModel(BaseModel):

    """Test model for compatibility testing."""

    email: str
    age: int

    @field_validator("email", mode="before")
    @classmethod
    def validate_email(cls, v):

        """Test validator."""
        if "@" not in str(v):
            raise ValueError("Invalid email")
        return v

        @field_validator("age")
        @classmethod
    def validate_age(cls, v):

        """Test validator without mode parameter."""
        if v < 0:
            raise ValueError("Age must be positive")
        return v


    def test_pydantic_compatibility():

        """Test that our compatibility layer works."""
    # Test successful validation
        model = TestModel(email="test@example.com", age=25)
        assert model.email == "test@example.com"
        assert model.age == 25

    # Test email validation
        with pytest.raises(ValueError, match="Invalid email"):
        TestModel(email="invalid-email", age=25)

    # Test age validation
        with pytest.raises(ValueError, match="Age must be positive"):
        TestModel(email="test@example.com", age=-1)


    def test_pydantic_version_detection():

        """Test that we can detect Pydantic version."""
        assert isinstance(PYDANTIC_V2, bool)
    # In our current setup, this should be True
        assert PYDANTIC_V2 is True
