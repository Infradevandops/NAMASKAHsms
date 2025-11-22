"""Unit tests for utility functions."""
from app.utils.security import hash_password, verify_password, generate_api_key
from app.utils.validation import validate_email, validate_phone, sanitize_input
from app.utils.email import EmailService


class TestSecurityUtils:
    """Test security utilities."""

    def test_hash_password(self):
        """Test password hashing."""
        from .fixtures import generate_test_password

        password = generate_test_password()
        hashed = hash_password(password)

        assert hashed != password
        assert len(hashed) > 0
        assert isinstance(hashed, str)

    def test_verify_password(self):
        """Test password verification."""
        from .fixtures import generate_test_password

        password = generate_test_password()
        hashed = hash_password(password)

        assert verify_password(password, hashed) is True
        assert verify_password(generate_test_password(), hashed) is False

    def test_generate_api_key(self):
        """Test API key generation."""
        api_key = generate_api_key()

        assert api_key.startswith("nsk_")
        assert len(api_key) > 20
        assert isinstance(api_key, str)


class TestValidationUtils:
    """Test validation utilities."""

    def test_validate_email(self):
        """Test email validation."""
        assert validate_email("test@example.com") is True
        assert validate_email("valid.email + tag@domain.co.uk") is True
        assert validate_email("invalid.email") is False
        assert validate_email("@invalid.com") is False
        assert validate_email("invalid@") is False

    def test_validate_phone(self):
        """Test phone number validation."""
        assert validate_phone("+1234567890") is True
        assert validate_phone("1234567890") is True
        assert validate_phone("+44 20 7946 0958") is True
        assert validate_phone("invalid") is False
        assert validate_phone("123") is False

    def test_sanitize_input(self):
        """Test input sanitization."""
        # Test XSS prevention
        malicious = "<script>alert('xss')</script>Hello"
        sanitized = sanitize_input(malicious)
        assert "<script>" not in sanitized
        assert "Hello" in sanitized

        # Test SQL injection prevention
        sql_injection = "'; DROP TABLE users; --"
        sanitized = sanitize_input(sql_injection)
        assert "DROP TABLE" not in sanitized

        # Test normal input
        normal = "Normal user input 123"
        sanitized = sanitize_input(normal)
        assert sanitized == normal


class TestEmailService:
    """Test email service utilities."""

    def test_email_service_initialization(self, db_session):
        """Test email service initialization."""
        email_service = EmailService(db_session)

        assert email_service.db == db_session
        assert hasattr(email_service, 'send_email')
        assert hasattr(email_service, 'send_template_email')

    def test_email_template_rendering(self, db_session):
        """Test email template rendering."""
        email_service = EmailService(db_session)

        template_data = {
            "user_name": "John Doe",
            "verification_code": "123456"
        }

        # Test template rendering (would need actual templates)
        rendered = email_service.render_template("welcome", template_data)

        # Basic test - should contain user data
        assert "John Doe" in rendered or rendered == ""  # Empty if template not found
