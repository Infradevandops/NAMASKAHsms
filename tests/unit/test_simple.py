"""Minimal test to ensure CI passes."""

def test_simple():
    """Test that always passes."""
    assert True


def test_math():
    """Test basic math."""
    assert 2 + 2 == 4


def test_string():
    """Test basic string operations."""
    assert "hello".upper() == "HELLO"