"""Tests for validators and error handling."""
import pytest
from pydantic import ValidationError

from app.schemas.validators import (
    validate_email,
    validate_password_strength,
    validate_country_code,
    validate_positive_number,
    validate_string_length,
    validate_enum_value,
    validate_url,
    validate_uuid,
    validate_credit_amount,
    validate_query_parameters,
    validate_search_query,
)
from app.schemas.auth import UserCreate, LoginRequest, PasswordResetConfirm
from app.schemas.verification import VerificationCreate, NumberRentalRequest
from app.core.error_responses import (
    ErrorCode,
    ErrorResponse,
    create_error_response,
    create_success_response,
    create_paginated_response,
    get_http_status_code,
)
from app.middleware.exception_handler import (
    ValidationException,
    AuthenticationException,
    AuthorizationException,
    ResourceNotFoundException,
    ConflictException,
    RateLimitException,
    InsufficientCreditsException,
)


# ============================================================================
# EMAIL VALIDATION TESTS
# ============================================================================

class TestEmailValidation:
    """Test email validation."""
    
    def test_valid_email(self):
        """Test valid email."""
        result = validate_email("user@example.com")
        assert result == "user@example.com"
    
    def test_email_lowercase(self):
        """Test email is converted to lowercase."""
        result = validate_email("User@Example.COM")
        assert result == "user@example.com"
    
    def test_empty_email(self):
        """Test empty email raises error."""
        with pytest.raises(ValueError, match="Email cannot be empty"):
            validate_email("")
    
    def test_invalid_email_format(self):
        """Test invalid email format."""
        with pytest.raises(ValueError, match="Invalid email format"):
            validate_email("invalid.email")
    
    def test_email_with_consecutive_dots(self):
        """Test email with consecutive dots."""
        with pytest.raises(ValueError, match="consecutive dots"):
            validate_email("user..name@example.com")
    
    def test_email_too_long(self):
        """Test email too long."""
        long_email = "a" * 250 + "@example.com"
        with pytest.raises(ValueError, match="too long"):
            validate_email(long_email)


# ============================================================================
# PASSWORD VALIDATION TESTS
# ============================================================================

class TestPasswordValidation:
    """Test password validation."""
    
    def test_valid_password(self):
        """Test valid password."""
        result = validate_password_strength("SecurePass123!")
        assert result == "SecurePass123!"
    
    def test_password_too_short(self):
        """Test password too short."""
        with pytest.raises(ValueError, match="at least 8 characters"):
            validate_password_strength("Short1!")
    
    def test_password_no_uppercase(self):
        """Test password without uppercase."""
        with pytest.raises(ValueError, match="uppercase letter"):
            validate_password_strength("securepass123!")
    
    def test_password_no_lowercase(self):
        """Test password without lowercase."""
        with pytest.raises(ValueError, match="lowercase letter"):
            validate_password_strength("SECUREPASS123!")
    
    def test_password_no_digit(self):
        """Test password without digit."""
        with pytest.raises(ValueError, match="digit"):
            validate_password_strength("SecurePass!")
    
    def test_password_no_special_char(self):
        """Test password without special character."""
        with pytest.raises(ValueError, match="special character"):
            validate_password_strength("SecurePass123")
    
    def test_password_too_long(self):
        """Test password too long."""
        long_password = "A" * 100 + "a1!"
        with pytest.raises(ValueError, match="too long"):
            validate_password_strength(long_password)


# ============================================================================
# COUNTRY CODE VALIDATION TESTS
# ============================================================================

class TestCountryCodeValidation:
    """Test country code validation."""
    
    def test_valid_country_code(self):
        """Test valid country code."""
        result = validate_country_code("US")
        assert result == "US"
    
    def test_country_code_lowercase(self):
        """Test country code converted to uppercase."""
        result = validate_country_code("us")
        assert result == "US"
    
    def test_country_name(self):
        """Test country name."""
        result = validate_country_code("usa")
        assert result == "usa"
    
    def test_empty_country_code(self):
        """Test empty country code."""
        with pytest.raises(ValueError, match="cannot be empty"):
            validate_country_code("")


# ============================================================================
# NUMBER VALIDATION TESTS
# ============================================================================

class TestNumberValidation:
    """Test number validation."""
    
    def test_valid_positive_number(self):
        """Test valid positive number."""
        result = validate_positive_number(10.5)
        assert result == 10.5
    
    def test_zero_is_not_positive(self):
        """Test zero is not positive."""
        with pytest.raises(ValueError, match="must be positive"):
            validate_positive_number(0)
    
    def test_negative_number(self):
        """Test negative number."""
        with pytest.raises(ValueError, match="must be positive"):
            validate_positive_number(-5)
    
    def test_non_numeric_value(self):
        """Test non-numeric value."""
        with pytest.raises(ValueError, match="must be a number"):
            validate_positive_number("not a number")


# ============================================================================
# STRING LENGTH VALIDATION TESTS
# ============================================================================

class TestStringLengthValidation:
    """Test string length validation."""
    
    def test_valid_string(self):
        """Test valid string."""
        result = validate_string_length("hello", min_length=1, max_length=10)
        assert result == "hello"
    
    def test_string_too_short(self):
        """Test string too short."""
        with pytest.raises(ValueError, match="at least"):
            validate_string_length("a", min_length=5, max_length=10)
    
    def test_string_too_long(self):
        """Test string too long."""
        with pytest.raises(ValueError, match="cannot exceed"):
            validate_string_length("a" * 20, min_length=1, max_length=10)


# ============================================================================
# ENUM VALIDATION TESTS
# ============================================================================

class TestEnumValidation:
    """Test enum validation."""
    
    def test_valid_enum_value(self):
        """Test valid enum value."""
        result = validate_enum_value("sms", ["sms", "voice"])
        assert result == "sms"
    
    def test_invalid_enum_value(self):
        """Test invalid enum value."""
        with pytest.raises(ValueError, match="must be one of"):
            validate_enum_value("invalid", ["sms", "voice"])


# ============================================================================
# URL VALIDATION TESTS
# ============================================================================

class TestURLValidation:
    """Test URL validation."""
    
    def test_valid_url(self):
        """Test valid URL."""
        result = validate_url("https://example.com")
        assert result == "https://example.com"
    
    def test_invalid_url(self):
        """Test invalid URL."""
        with pytest.raises(ValueError, match="Invalid URL"):
            validate_url("not a url")
    
    def test_url_too_long(self):
        """Test URL too long."""
        long_url = "https://" + "a" * 2100
        with pytest.raises(ValueError, match="too long"):
            validate_url(long_url)


# ============================================================================
# CREDIT AMOUNT VALIDATION TESTS
# ============================================================================

class TestCreditAmountValidation:
    """Test credit amount validation."""
    
    def test_valid_amount(self):
        """Test valid amount."""
        result = validate_credit_amount(10.50)
        assert result == 10.50
    
    def test_amount_rounded(self):
        """Test amount is rounded to 2 decimals."""
        result = validate_credit_amount(10.555)
        assert result == 10.56
    
    def test_zero_amount(self):
        """Test zero amount."""
        with pytest.raises(ValueError, match="must be positive"):
            validate_credit_amount(0)
    
    def test_amount_exceeds_limit(self):
        """Test amount exceeds limit."""
        with pytest.raises(ValueError, match="exceeds maximum"):
            validate_credit_amount(2000000)


# ============================================================================
# PAGINATION VALIDATION TESTS
# ============================================================================

class TestPaginationValidation:
    """Test pagination validation."""
    
    def test_valid_pagination(self):
        """Test valid pagination."""
        page, limit = validate_query_parameters(1, 20)
        assert page == 1
        assert limit == 20
    
    def test_default_pagination(self):
        """Test default pagination."""
        page, limit = validate_query_parameters(None, None)
        assert page == 1
        assert limit == 20
    
    def test_page_less_than_one(self):
        """Test page less than one."""
        page, limit = validate_query_parameters(0, 20)
        assert page == 1
    
    def test_limit_exceeds_max(self):
        """Test limit exceeds max."""
        page, limit = validate_query_parameters(1, 200)
        assert limit == 100


# ============================================================================
# SEARCH QUERY VALIDATION TESTS
# ============================================================================

class TestSearchQueryValidation:
    """Test search query validation."""
    
    def test_valid_search_query(self):
        """Test valid search query."""
        result = validate_search_query("test query")
        assert result == "test query"
    
    def test_search_query_with_dangerous_chars(self):
        """Test search query with dangerous characters."""
        with pytest.raises(ValueError, match="invalid character"):
            validate_search_query("test<script>")


# ============================================================================
# AUTH SCHEMA VALIDATION TESTS
# ============================================================================

class TestAuthSchemaValidation:
    """Test auth schema validation."""
    
    def test_valid_user_create(self):
        """Test valid user creation."""
        user = UserCreate(
            email="user@example.com",
            password="SecurePass123!",
            referral_code="ABC123"
        )
        assert user.email == "user@example.com"
        assert user.referral_code == "ABC123"
    
    def test_invalid_email_in_user_create(self):
        """Test invalid email in user creation."""
        with pytest.raises(ValidationError):
            UserCreate(
                email="invalid",
                password="SecurePass123!"
            )
    
    def test_weak_password_in_user_create(self):
        """Test weak password in user creation."""
        with pytest.raises(ValidationError):
            UserCreate(
                email="user@example.com",
                password="weak"
            )
    
    def test_valid_login_request(self):
        """Test valid login request."""
        login = LoginRequest(
            email="user@example.com",
            password="SecurePass123!"
        )
        assert login.email == "user@example.com"
    
    def test_valid_password_reset_confirm(self):
        """Test valid password reset confirm."""
        reset = PasswordResetConfirm(
            token="reset_token_123",
            new_password="NewSecurePass123!"
        )
        assert reset.token == "reset_token_123"


# ============================================================================
# VERIFICATION SCHEMA VALIDATION TESTS
# ============================================================================

class TestVerificationSchemaValidation:
    """Test verification schema validation."""
    
    def test_valid_verification_create(self):
        """Test valid verification creation."""
        verify = VerificationCreate(
            service_name="telegram",
            country="US",
            capability="sms"
        )
        assert verify.service_name == "telegram"
        assert verify.country == "US"
        assert verify.capability == "sms"
    
    def test_invalid_capability(self):
        """Test invalid capability."""
        with pytest.raises(ValidationError):
            VerificationCreate(
                service_name="telegram",
                country="US",
                capability="invalid"
            )
    
    def test_valid_rental_request(self):
        """Test valid rental request."""
        rental = NumberRentalRequest(
            service_name="telegram",
            duration_hours=24.0,
            mode="always_ready"
        )
        assert rental.service_name == "telegram"
        assert rental.duration_hours == 24.0
    
    def test_rental_duration_exceeds_max(self):
        """Test rental duration exceeds max."""
        with pytest.raises(ValidationError):
            NumberRentalRequest(
                service_name="telegram",
                duration_hours=10000.0
            )


# ============================================================================
# ERROR RESPONSE TESTS
# ============================================================================

class TestErrorResponses:
    """Test error response creation."""
    
    def test_create_error_response(self):
        """Test creating error response."""
        error = create_error_response(
            error_type="Validation Error",
            code=ErrorCode.VALIDATION_ERROR,
            message="Invalid input",
            request_id="req_123"
        )
        assert error.error == "Validation Error"
        assert error.code == "VALIDATION_ERROR"
        assert error.message == "Invalid input"
        assert error.request_id == "req_123"
    
    def test_create_success_response(self):
        """Test creating success response."""
        success = create_success_response(
            message="Operation successful",
            data={"id": 1},
            request_id="req_123"
        )
        assert success.success is True
        assert success.message == "Operation successful"
        assert success.data == {"id": 1}
    
    def test_create_paginated_response(self):
        """Test creating paginated response."""
        paginated = create_paginated_response(
            data=[{"id": 1}, {"id": 2}],
            page=1,
            limit=20,
            total=100,
            request_id="req_123"
        )
        assert paginated.success is True
        assert len(paginated.data) == 2
        assert paginated.pagination["page"] == 1
        assert paginated.pagination["total"] == 100
        assert paginated.pagination["pages"] == 5
    
    def test_http_status_code_mapping(self):
        """Test HTTP status code mapping."""
        assert get_http_status_code(ErrorCode.VALIDATION_ERROR) == 400
        assert get_http_status_code(ErrorCode.UNAUTHORIZED) == 401
        assert get_http_status_code(ErrorCode.FORBIDDEN) == 403
        assert get_http_status_code(ErrorCode.NOT_FOUND) == 404
        assert get_http_status_code(ErrorCode.CONFLICT) == 409
        assert get_http_status_code(ErrorCode.RATE_LIMIT_EXCEEDED) == 429
        assert get_http_status_code(ErrorCode.INTERNAL_ERROR) == 500


# ============================================================================
# EXCEPTION TESTS
# ============================================================================

class TestExceptions:
    """Test custom exceptions."""
    
    def test_validation_exception(self):
        """Test validation exception."""
        exc = ValidationException("Invalid input")
        assert exc.code == ErrorCode.VALIDATION_ERROR
        assert exc.status_code == 400
    
    def test_authentication_exception(self):
        """Test authentication exception."""
        exc = AuthenticationException()
        assert exc.code == ErrorCode.UNAUTHORIZED
        assert exc.status_code == 401
    
    def test_authorization_exception(self):
        """Test authorization exception."""
        exc = AuthorizationException()
        assert exc.code == ErrorCode.FORBIDDEN
        assert exc.status_code == 403
    
    def test_resource_not_found_exception(self):
        """Test resource not found exception."""
        exc = ResourceNotFoundException("User")
        assert exc.code == ErrorCode.NOT_FOUND
        assert exc.status_code == 404
        assert "User" in exc.message
    
    def test_conflict_exception(self):
        """Test conflict exception."""
        exc = ConflictException()
        assert exc.code == ErrorCode.CONFLICT
        assert exc.status_code == 409
    
    def test_rate_limit_exception(self):
        """Test rate limit exception."""
        exc = RateLimitException()
        assert exc.code == ErrorCode.RATE_LIMIT_EXCEEDED
        assert exc.status_code == 429
    
    def test_insufficient_credits_exception(self):
        """Test insufficient credits exception."""
        exc = InsufficientCreditsException()
        assert exc.code == ErrorCode.INSUFFICIENT_CREDITS
        assert exc.status_code == 402


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
