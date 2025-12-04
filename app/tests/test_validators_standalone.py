"""Standalone validator tests that don't require app initialization."""
import sys
import re
from typing import Optional

# Test validators directly without importing from app
def validate_email(email: str) -> str:
    """Validate email address."""
    if not email:
        raise ValueError("Email cannot be empty")
    
    email = email.lower().strip()
    
    # RFC 5322 simplified pattern
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if not re.match(pattern, email):
        raise ValueError("Invalid email format")
    
    if ".." in email:
        raise ValueError("Email cannot contain consecutive dots")
    
    if len(email) > 254:
        raise ValueError("Email is too long")
    
    return email


def validate_password_strength(password: str) -> str:
    """Validate password strength."""
    if len(password) < 8:
        raise ValueError("Password must be at least 8 characters")
    
    if not any(c.isupper() for c in password):
        raise ValueError("Password must contain uppercase letter")
    
    if not any(c.islower() for c in password):
        raise ValueError("Password must contain lowercase letter")
    
    if not any(c.isdigit() for c in password):
        raise ValueError("Password must contain digit")
    
    if not any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in password):
        raise ValueError("Password must contain special character")
    
    if len(password) > 128:
        raise ValueError("Password is too long")
    
    return password


# Tests
def test_valid_email():
    """Test valid email."""
    result = validate_email("user@example.com")
    assert result == "user@example.com"
    print("✓ test_valid_email passed")


def test_email_lowercase():
    """Test email is converted to lowercase."""
    result = validate_email("User@Example.COM")
    assert result == "user@example.com"
    print("✓ test_email_lowercase passed")


def test_empty_email():
    """Test empty email raises error."""
    try:
        validate_email("")
        assert False, "Should have raised ValueError"
    except ValueError as e:
        assert "cannot be empty" in str(e)
        print("✓ test_empty_email passed")


def test_invalid_email_format():
    """Test invalid email format."""
    try:
        validate_email("invalid.email")
        assert False, "Should have raised ValueError"
    except ValueError as e:
        assert "Invalid email format" in str(e)
        print("✓ test_invalid_email_format passed")


def test_valid_password():
    """Test valid password."""
    result = validate_password_strength("SecurePass123!")
    assert result == "SecurePass123!"
    print("✓ test_valid_password passed")


def test_password_too_short():
    """Test password too short."""
    try:
        validate_password_strength("Short1!")
        assert False, "Should have raised ValueError"
    except ValueError as e:
        assert "at least 8 characters" in str(e)
        print("✓ test_password_too_short passed")


def test_password_no_uppercase():
    """Test password without uppercase."""
    try:
        validate_password_strength("securepass123!")
        assert False, "Should have raised ValueError"
    except ValueError as e:
        assert "uppercase letter" in str(e)
        print("✓ test_password_no_uppercase passed")


def test_password_no_lowercase():
    """Test password without lowercase."""
    try:
        validate_password_strength("SECUREPASS123!")
        assert False, "Should have raised ValueError"
    except ValueError as e:
        assert "lowercase letter" in str(e)
        print("✓ test_password_no_lowercase passed")


def test_password_no_digit():
    """Test password without digit."""
    try:
        validate_password_strength("SecurePass!")
        assert False, "Should have raised ValueError"
    except ValueError as e:
        assert "digit" in str(e)
        print("✓ test_password_no_digit passed")


def test_password_no_special_char():
    """Test password without special character."""
    try:
        validate_password_strength("SecurePass123")
        assert False, "Should have raised ValueError"
    except ValueError as e:
        assert "special character" in str(e)
        print("✓ test_password_no_special_char passed")


if __name__ == "__main__":
    print("Running standalone validator tests...\n")
    
    test_valid_email()
    test_email_lowercase()
    test_empty_email()
    test_invalid_email_format()
    test_valid_password()
    test_password_too_short()
    test_password_no_uppercase()
    test_password_no_lowercase()
    test_password_no_digit()
    test_password_no_special_char()
    
    print("\n✅ All standalone tests passed!")
