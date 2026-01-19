"""Tests for response schema validators.

Feature: tier-system-rbac
Tests validate that API response schemas correctly validate response structures.
"""

import pytest

from app.schemas.tier import (
    AnalyticsSummaryResponse,
    CurrentTierResponse,
    DashboardActivity,
    DashboardActivityResponse,
    TiersListResponse,
)
from app.utils.response_validator import (
    ResponseValidationError,
    check_required_fields,
    validate_response,
    validate_response_safe,
)


class TestTiersListResponseValidator:
    """Tests for /api/tiers/ response validation."""

    def test_valid_tiers_list_response(self):
        """Test that valid tiers list response passes validation."""
        data = {
            "tiers": [
                {
                    "tier": "freemium",
                    "name": "Freemium",
                    "price_monthly": 0.0,
                    "price_display": "Free",
                    "quota_usd": 0.0,
                    "overage_rate": 0.0,
                    "features": {
                        "api_access": False,
                        "area_code_selection": False,
                        "isp_filtering": False,
                        "api_key_limit": 0,
                        "support_level": "community",
                    },
                },
                {
                    "tier": "payg",
                    "name": "Pay-As-You-Go",
                    "price_monthly": 0.0,
                    "price_display": "Free",
                    "quota_usd": 100.0,
                    "overage_rate": 0.05,
                    "features": {
                        "api_access": True,
                        "area_code_selection": True,
                        "isp_filtering": False,
                        "api_key_limit": 5,
                        "support_level": "email",
                    },
                },
                {
                    "tier": "pro",
                    "name": "Pro",
                    "price_monthly": 99.0,
                    "price_display": "$99.00/mo",
                    "quota_usd": 500.0,
                    "overage_rate": 0.03,
                    "features": {
                        "api_access": True,
                        "area_code_selection": True,
                        "isp_filtering": True,
                        "api_key_limit": 20,
                        "support_level": "priority",
                    },
                },
                {
                    "tier": "custom",
                    "name": "Custom",
                    "price_monthly": 0.0,
                    "price_display": "Contact Us",
                    "quota_usd": 10000.0,
                    "overage_rate": 0.01,
                    "features": {
                        "api_access": True,
                        "area_code_selection": True,
                        "isp_filtering": True,
                        "api_key_limit": -1,
                        "support_level": "priority",
                    },
                },
            ]
        }

        validated = validate_response(data, TiersListResponse)
        assert validated is not None
        assert len(validated.tiers) == 4

    def test_invalid_tier_count_fails(self):
        """Test that wrong number of tiers fails validation."""
        data = {
            "tiers": [
                {
                    "tier": "freemium",
                    "name": "Freemium",
                    "price_monthly": 0.0,
                    "price_display": "Free",
                    "quota_usd": 0.0,
                    "overage_rate": 0.0,
                    "features": {
                        "api_access": False,
                        "area_code_selection": False,
                        "isp_filtering": False,
                        "api_key_limit": 0,
                        "support_level": "community",
                    },
                }
            ]
        }

        with pytest.raises(ResponseValidationError):
            validate_response(data, TiersListResponse)

    def test_invalid_tier_name_fails(self):
        """Test that invalid tier name fails validation."""
        data = {
            "tiers": [
                {
                    "tier": "invalid_tier",
                    "name": "Invalid",
                    "price_monthly": 0.0,
                    "price_display": "Free",
                    "quota_usd": 0.0,
                    "overage_rate": 0.0,
                    "features": {
                        "api_access": False,
                        "area_code_selection": False,
                        "isp_filtering": False,
                        "api_key_limit": 0,
                        "support_level": "community",
                    },
                }
            ]
            * 4
        }

        with pytest.raises(ResponseValidationError):
            validate_response(data, TiersListResponse)


class TestCurrentTierResponseValidator:
    """Tests for /api/tiers/current response validation."""

    def test_valid_current_tier_response(self):
        """Test that valid current tier response passes validation."""
        data = {
            "current_tier": "freemium",
            "tier_name": "Freemium",
            "price_monthly": 0.0,
            "quota_usd": 0.0,
            "quota_used_usd": 0.0,
            "quota_remaining_usd": 0.0,
            "sms_count": 0,
            "within_quota": True,
            "overage_rate": 0.0,
            "features": {
                "api_access": False,
                "area_code_selection": False,
                "isp_filtering": False,
                "api_key_limit": 0,
                "support_level": "community",
            },
        }

        validated = validate_response(data, CurrentTierResponse)
        assert validated is not None
        assert validated.current_tier == "freemium"

    def test_missing_required_field_fails(self):
        """Test that missing required field fails validation."""
        data = {
            "current_tier": "freemium",
            "tier_name": "Freemium",
            # Missing price_monthly
            "quota_usd": 0.0,
            "quota_used_usd": 0.0,
            "quota_remaining_usd": 0.0,
            "sms_count": 0,
            "within_quota": True,
            "overage_rate": 0.0,
            "features": {
                "api_access": False,
                "area_code_selection": False,
                "isp_filtering": False,
                "api_key_limit": 0,
                "support_level": "community",
            },
        }

        with pytest.raises(ResponseValidationError):
            validate_response(data, CurrentTierResponse)

    def test_negative_values_fail(self):
        """Test that negative values fail validation."""
        data = {
            "current_tier": "freemium",
            "tier_name": "Freemium",
            "price_monthly": -10.0,  # Negative price
            "quota_usd": 0.0,
            "quota_used_usd": 0.0,
            "quota_remaining_usd": 0.0,
            "sms_count": 0,
            "within_quota": True,
            "overage_rate": 0.0,
            "features": {
                "api_access": False,
                "area_code_selection": False,
                "isp_filtering": False,
                "api_key_limit": 0,
                "support_level": "community",
            },
        }

        with pytest.raises(ResponseValidationError):
            validate_response(data, CurrentTierResponse)


class TestAnalyticsSummaryResponseValidator:
    """Tests for /api/analytics/summary response validation."""

    def test_valid_analytics_summary_response(self):
        """Test that valid analytics summary response passes validation."""
        data = {
            "total_verifications": 100,
            "successful_verifications": 80,
            "failed_verifications": 15,
            "pending_verifications": 5,
            "success_rate": 0.8,
            "total_spent": 50.0,
            "revenue": 50.0,
            "average_cost": 0.5,
            "recent_activity": 30,
            "monthly_verifications": 100,
            "monthly_spent": 50.0,
            "last_updated": "2024-01-01T00:00:00",
        }

        validated = validate_response(data, AnalyticsSummaryResponse)
        assert validated is not None
        assert validated.total_verifications == 100

    def test_invalid_success_rate_fails(self):
        """Test that success rate outside 0-1 range fails validation."""
        data = {
            "total_verifications": 100,
            "successful_verifications": 80,
            "failed_verifications": 15,
            "pending_verifications": 5,
            "success_rate": 1.5,  # Invalid: > 1
            "total_spent": 50.0,
            "revenue": 50.0,
            "average_cost": 0.5,
            "recent_activity": 30,
            "monthly_verifications": 100,
            "monthly_spent": 50.0,
            "last_updated": "2024-01-01T00:00:00",
        }

        with pytest.raises(ResponseValidationError):
            validate_response(data, AnalyticsSummaryResponse)


class TestDashboardActivityResponseValidator:
    """Tests for /api/dashboard/activity/recent response validation."""

    def test_valid_dashboard_activity_response(self):
        """Test that valid dashboard activity response passes validation."""
        data = [
            {
                "id": "activity_1",
                "service_name": "sms",
                "phone_number": "+1234567890",
                "status": "completed",
                "created_at": "2024-01-01T00:00:00",
            },
            {
                "id": "activity_2",
                "service_name": "sms",
                "phone_number": "+1234567891",
                "status": "pending",
                "created_at": "2024-01-01T00:01:00",
            },
        ]

        # Validate each item in the list
        from pydantic import parse_obj_as

        validated = parse_obj_as(DashboardActivityResponse, data)
        assert validated is not None
        assert len(validated) == 2

    def test_invalid_status_fails(self):
        """Test that invalid status fails validation."""
        data = [
            {
                "id": "activity_1",
                "service_name": "sms",
                "phone_number": "+1234567890",
                "status": "invalid_status",
                "created_at": "2024-01-01T00:00:00",
            }
        ]

        from pydantic import ValidationError, parse_obj_as

        with pytest.raises(ValidationError):
            parse_obj_as(DashboardActivityResponse, data)


class TestResponseValidatorUtilities:
    """Tests for response validator utility functions."""

    def test_validate_response_safe_success(self):
        """Test safe validation with valid data."""
        data = {
            "id": "activity_1",
            "service_name": "sms",
            "phone_number": "+1234567890",
            "status": "completed",
            "created_at": "2024-01-01T00:00:00",
        }

        is_valid, validated, error = validate_response_safe(data, DashboardActivity)
        assert is_valid is True
        assert validated is not None
        assert error is None

    def test_validate_response_safe_failure(self):
        """Test safe validation with invalid data."""
        data = {
            "id": "activity_1",
            # Missing required fields
        }

        is_valid, validated, error = validate_response_safe(data, DashboardActivity)
        assert is_valid is False
        assert validated is None
        assert error is not None

    def test_check_required_fields_all_present(self):
        """Test checking required fields when all are present."""
        data = {"field1": "value1", "field2": "value2", "field3": "value3"}

        all_present, missing = check_required_fields(
            data, ["field1", "field2", "field3"]
        )
        assert all_present is True
        assert len(missing) == 0

    def test_check_required_fields_some_missing(self):
        """Test checking required fields when some are missing."""
        data = {"field1": "value1", "field3": "value3"}

        all_present, missing = check_required_fields(
            data, ["field1", "field2", "field3"]
        )
        assert all_present is False
        assert "field2" in missing
        assert len(missing) == 1
