"""Tests for Pydantic schemas and validation."""
from datetime import datetime

import pytest
from pydantic import ValidationError

from app.schemas import (LoginRequest, PaymentInitialize, UserCreate,
                         VerificationCreate, sanitize_input,
                         validate_currency_amount, validate_phone_number,
                         validate_service_name)


class TestAuthSchemas:
    """Test authentication schemas."""

    def test_user_create_valid(self):
        """Test valid user creation schema."""
        data = {
            "email": "test@example.com",
            "password": "password123",
            "referral_code": "ABC123"
        }

        user = UserCreate(**data)

        assert user.email == "test@example.com"
        assert user.password == "password123"
        assert user.referral_code == "ABC123"

    def test_user_create_invalid_email(self):
        """Test user creation with invalid email."""
        data = {
            "email": "invalid-email",
            "password": "password123"
        }

        with pytest.raises(ValidationError) as exc_info:
            UserCreate(**data)

        assert "email" in str(exc_info.value)

    def test_user_create_weak_password(self):
        """Test user creation with weak password."""
        data = {
            "email": "test@example.com",
            "password": "123"
        }

        with pytest.raises(ValidationError) as exc_info:
            UserCreate(**data)

        assert "Password must be at least 6 characters" in str(exc_info.value)

    def test_login_request_valid(self):
        """Test valid login request schema."""
        data = {
            "email": "test@example.com",
            "password": "password123"
        }

        login = LoginRequest(**data)

        assert login.email == "test@example.com"
        assert login.password == "password123"


class TestVerificationSchemas:
    """Test verification schemas."""

    def test_verification_create_valid(self):
        """Test valid verification creation schema."""
        data = {
            "service_name": "telegram",
            "capability": "sms",
            "area_code": "212",
            "carrier": "verizon"
        }

        verification = VerificationCreate(**data)

        assert verification.service_name == "telegram"
        assert verification.capability == "sms"
        assert verification.area_code == "212"
        assert verification.carrier == "verizon"

    def test_verification_create_invalid_capability(self):
        """Test verification creation with invalid capability."""
        data = {
            "service_name": "telegram",
            "capability": "invalid"
        }

        with pytest.raises(ValidationError) as exc_info:
            VerificationCreate(**data)

        assert "Capability must be sms or voice" in str(exc_info.value)

    def test_verification_create_empty_service(self):
        """Test verification creation with empty service name."""
        data = {
            "service_name": "",
            "capability": "sms"
        }

        with pytest.raises(ValidationError) as exc_info:
            VerificationCreate(**data)

        assert "Service name cannot be empty" in str(exc_info.value)

    def test_verification_create_service_name_normalization(self):
        """Test service name normalization."""
        data = {
            "service_name": "  TELEGRAM  ",
            "capability": "sms"
        }

        verification = VerificationCreate(**data)

        assert verification.service_name == "telegram"


class TestPaymentSchemas:
    """Test payment schemas."""

    def test_payment_initialize_valid(self):
        """Test valid payment initialization schema."""
        data = {
            "amount_usd": 20.0,
            "payment_method": "paystack"
        }

        payment = PaymentInitialize(**data)

        assert payment.amount_usd == 20.0
        assert payment.payment_method == "paystack"

    def test_payment_initialize_minimum_amount(self):
        """Test payment initialization with amount below minimum."""
        data = {
            "amount_usd": 2.0,
            "payment_method": "paystack"
        }

        with pytest.raises(ValidationError) as exc_info:
            PaymentInitialize(**data)

        assert "Minimum payment amount is $5 USD" in str(exc_info.value)

    def test_payment_initialize_maximum_amount(self):
        """Test payment initialization with amount above maximum."""
        data = {
            "amount_usd": 15000.0,
            "payment_method": "paystack"
        }

        with pytest.raises(ValidationError) as exc_info:
            PaymentInitialize(**data)

        assert "Maximum payment amount is $10,000 USD" in str(exc_info.value)

    def test_payment_initialize_invalid_method(self):
        """Test payment initialization with invalid method."""
        data = {
            "amount_usd": 20.0,
            "payment_method": "bitcoin"
        }

        with pytest.raises(ValidationError) as exc_info:
            PaymentInitialize(**data)

        assert "Only paystack payment method is supported" in str(exc_info.value)


class TestValidationUtilities:
    """Test validation utility functions."""

    def test_validate_phone_number_valid(self):
        """Test valid phone number validation."""
        valid_numbers = [
            "+1234567890",
            "+12345678901",
            "+123456789012345"
        ]

        for number in valid_numbers:
            result = validate_phone_number(number)
            assert result == number

    def test_validate_phone_number_invalid(self):
        """Test invalid phone number validation."""
        invalid_numbers = [
            "1234567890",  # Missing +
            "+123",        # Too short
            "+1234567890123456",  # Too long
            "abc123",      # Contains letters
            ""             # Empty
        ]

        for number in invalid_numbers:
            with pytest.raises(ValueError):
                validate_phone_number(number)

    def test_validate_service_name_valid(self):
        """Test valid service name validation."""
        valid_names = [
            "telegram",
            "whatsapp",
            "discord-bot",
            "service_123"
        ]

        for name in valid_names:
            result = validate_service_name(name)
            assert result == name.lower()

    def test_validate_service_name_invalid(self):
        """Test invalid service name validation."""
        invalid_names = [
            "",           # Empty
            "   ",        # Whitespace only
            "service@123",  # Invalid character
            "service 123"  # Space
        ]

        for name in invalid_names:
            with pytest.raises(ValueError):
                validate_service_name(name)

    def test_validate_currency_amount_valid(self):
        """Test valid currency amount validation."""
        valid_amounts = [10.0, 25.50, 100.99]

        for amount in valid_amounts:
            result = validate_currency_amount(amount)
            assert result == amount

    def test_validate_currency_amount_invalid(self):
        """Test invalid currency amount validation."""
        invalid_amounts = [0.0, -10.0, 200000.0]

        for amount in invalid_amounts:
            with pytest.raises(ValueError):
                validate_currency_amount(amount)

    def test_sanitize_input_safe(self):
        """Test input sanitization with safe content."""
        safe_inputs = [
            "Hello world",
            "User input 123",
            "Email: user@example.com"
        ]

        for input_text in safe_inputs:
            result = sanitize_input(input_text)
            assert result == input_text

    def test_sanitize_input_dangerous(self):
        """Test input sanitization with dangerous content."""
        dangerous_inputs = [
            "<script>alert('xss')</script>",
            "javascript:alert('xss')",
            "<iframe src='evil.com'></iframe>",
            "onclick='alert()'"
        ]

        for input_text in dangerous_inputs:
            result = sanitize_input(input_text)
            # Should remove dangerous content
            assert "<script>" not in result
            assert "javascript:" not in result
            assert "<iframe>" not in result
            assert "onclick=" not in result


class TestSchemaExamples:
    """Test that schema examples are valid."""

    def test_user_create_example(self):
        """Test UserCreate schema example."""
        example = UserCreate.Config.schema_extra["example"]
        user = UserCreate(**example)
        assert user.email == example["email"]

    def test_verification_create_example(self):
        """Test VerificationCreate schema example."""
        example = VerificationCreate.Config.schema_extra["example"]
        verification = VerificationCreate(**example)
        assert verification.service_name == example["service_name"]

    def test_payment_initialize_example(self):
        """Test PaymentInitialize schema example."""
        example = PaymentInitialize.Config.schema_extra["example"]
        payment = PaymentInitialize(**example)
        assert payment.amount_usd == example["amount_usd"]


class TestSchemaValidationEdgeCases:
    """Test edge cases in schema validation."""

    def test_optional_fields_none(self):
        """Test schemas with optional fields set to None."""
        data = {
            "service_name": "telegram",
            "capability": "sms",
            "area_code": None,
            "carrier": None
        }

        verification = VerificationCreate(**data)

        assert verification.area_code is None
        assert verification.carrier is None

    def test_default_values(self):
        """Test schemas with default values."""
        data = {
            "service_name": "telegram"
            # capability should default to "sms"
        }

        verification = VerificationCreate(**data)

        assert verification.capability == "sms"

    def test_field_aliases(self):
        """Test field aliases work correctly."""
        # Test that orm_mode works for response schemas
        from app.schemas.auth import UserResponse

        # This would typically come from a database model
        user_data = {
            "id": "user_123",
            "email": "test@example.com",
            "credits": 10.0,
            "free_verifications": 1.0,
            "is_admin": False,
            "email_verified": True,
            "referral_code": "ABC123",
            "created_at": datetime.now()
        }

        user_response = UserResponse(**user_data)

        assert user_response.id == "user_123"
        assert user_response.email == "test@example.com"
