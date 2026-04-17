"""
Unit tests for PhoneValidator service (Phase 3 - VOIP Rejection)
Tests phonenumbers integration for VOIP/landline detection
"""

import pytest

from app.services.phone_validator import PhoneValidator


class TestPhoneValidatorBasics:
    """Test basic phone validation functionality"""

    def test_validator_initialization(self):
        """Test PhoneValidator can be instantiated"""
        validator = PhoneValidator()
        assert validator is not None

    def test_valid_us_mobile_number(self):
        """Test valid US mobile number passes validation"""
        validator = PhoneValidator()
        result = validator.validate_mobile("+12025551234", "US")

        assert result["is_valid"] is True
        assert result["is_mobile"] is True
        assert result["is_voip"] is False
        assert result["number_type"] in ["MOBILE", "FIXED_LINE_OR_MOBILE"]

    def test_us_landline_rejected(self):
        """Test US landline number is rejected"""
        validator = PhoneValidator()
        # Use a known landline prefix (800 toll-free)
        result = validator.validate_mobile("+18005551234", "US")

        assert result["is_valid"] is True  # Valid format
        # Toll-free should not be mobile
        assert result["number_type"] in ["TOLL_FREE", "FIXED_LINE"]

    def test_invalid_phone_number(self):
        """Test invalid phone number format"""
        validator = PhoneValidator()
        result = validator.validate_mobile("+1234", "US")

        assert result["is_valid"] is False
        assert result["is_mobile"] is False


class TestPhoneValidatorVOIP:
    """Test VOIP detection (best-effort)"""

    def test_known_voip_prefix_detection(self):
        """Test detection of known VOIP prefixes"""
        validator = PhoneValidator()

        # Google Voice uses 747 area code
        result = validator.validate_mobile("+17475551234", "US")

        # Should flag as potential VOIP
        assert result.get("is_voip") is True or result.get("voip_risk") == "high"

    def test_regular_mobile_not_flagged_voip(self):
        """Test regular mobile numbers aren't flagged as VOIP"""
        validator = PhoneValidator()

        # Standard T-Mobile number
        result = validator.validate_mobile("+13105551234", "US")

        assert result.get("is_voip") is False
        assert result.get("voip_risk", "low") == "low"


class TestPhoneValidatorCountries:
    """Test multi-country support"""

    def test_uk_mobile_validation(self):
        """Test UK mobile number validation"""
        validator = PhoneValidator()
        # Use valid UK mobile prefix (07xxx)
        result = validator.validate_mobile("+447911123456", "GB")

        assert result["is_valid"] is True
        assert result["is_mobile"] is True

    def test_canada_mobile_validation(self):
        """Test Canada mobile number validation"""
        validator = PhoneValidator()
        result = validator.validate_mobile("+14165551234", "CA")

        assert result["is_valid"] is True
        # Canada uses FIXED_LINE_OR_MOBILE
        assert result["number_type"] in ["MOBILE", "FIXED_LINE_OR_MOBILE"]

    def test_invalid_country_code(self):
        """Test handling of invalid country code"""
        validator = PhoneValidator()
        result = validator.validate_mobile("+12025551234", "XX")

        # Should handle gracefully - may parse as US number
        assert "is_valid" in result
        assert "is_mobile" in result


class TestPhoneValidatorEdgeCases:
    """Test edge cases and error handling"""

    def test_none_phone_number(self):
        """Test None phone number handling"""
        validator = PhoneValidator()
        result = validator.validate_mobile(None, "US")

        assert result["is_valid"] is False
        assert result["is_mobile"] is False

    def test_empty_phone_number(self):
        """Test empty phone number handling"""
        validator = PhoneValidator()
        result = validator.validate_mobile("", "US")

        assert result["is_valid"] is False
        assert result["is_mobile"] is False

    def test_phone_without_plus_prefix(self):
        """Test phone number without + prefix"""
        validator = PhoneValidator()
        result = validator.validate_mobile("12025551234", "US")

        # Should handle gracefully
        assert "is_valid" in result
        assert "is_mobile" in result
