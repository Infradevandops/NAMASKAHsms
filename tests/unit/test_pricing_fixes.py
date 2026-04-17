"""Test pricing calculator bug fixes for v4.4.1."""

from unittest.mock import MagicMock, Mock, patch

import pytest

from app.services.pricing_calculator import PricingCalculator


def test_sprint_removed_from_carrier_premiums():
    """Verify Sprint is no longer in CARRIER_PREMIUMS."""
    assert "sprint" not in PricingCalculator.CARRIER_PREMIUMS
    assert "Sprint" not in PricingCalculator.CARRIER_PREMIUMS


def test_carrier_premiums_has_expected_carriers():
    """Verify expected carriers are present."""
    assert "verizon" in PricingCalculator.CARRIER_PREMIUMS
    assert "tmobile" in PricingCalculator.CARRIER_PREMIUMS
    assert "t-mobile" in PricingCalculator.CARRIER_PREMIUMS
    assert "att" in PricingCalculator.CARRIER_PREMIUMS
    assert "at&t" in PricingCalculator.CARRIER_PREMIUMS


def test_surcharge_breakdown_returned_for_payg_with_filters(mock_db_session):
    """Verify pricing returns surcharge breakdown for PAYG users."""
    # Mock user
    mock_user = Mock()
    mock_user.subscription_tier = "payg"
    mock_user.id = "test_user"

    # Mock DB query
    mock_db_session.query.return_value.filter.return_value.first.return_value = (
        mock_user
    )

    # Mock tier config
    with patch(
        "app.services.pricing_calculator.TierConfig.get_tier_config"
    ) as mock_tier:
        mock_tier.return_value = {
            "base_sms_cost": 2.50,
            "overage_rate": 2.50,
        }

        # Mock quota service
        with patch(
            "app.services.pricing_calculator.QuotaService.calculate_overage"
        ) as mock_quota:
            mock_quota.return_value = 0.0

            result = PricingCalculator.calculate_sms_cost(
                db=mock_db_session,
                user_id="test_user",
                filters={"carrier": "verizon", "area_code": "212"},
            )

    assert "carrier_surcharge" in result
    assert "area_code_surcharge" in result
    assert result["carrier_surcharge"] == 0.30  # Verizon premium
    assert result["area_code_surcharge"] == 0.50  # 212 premium


def test_surcharge_breakdown_zero_for_no_filters(mock_db_session):
    """Verify surcharge breakdown is zero when no filters applied."""
    mock_user = Mock()
    mock_user.subscription_tier = "payg"
    mock_user.id = "test_user"

    mock_db_session.query.return_value.filter.return_value.first.return_value = (
        mock_user
    )

    with patch(
        "app.services.pricing_calculator.TierConfig.get_tier_config"
    ) as mock_tier:
        mock_tier.return_value = {
            "base_sms_cost": 2.50,
            "overage_rate": 2.50,
        }

        with patch(
            "app.services.pricing_calculator.QuotaService.calculate_overage"
        ) as mock_quota:
            mock_quota.return_value = 0.0

            result = PricingCalculator.calculate_sms_cost(
                db=mock_db_session, user_id="test_user", filters={}
            )

    assert "carrier_surcharge" in result
    assert "area_code_surcharge" in result
    assert result["carrier_surcharge"] == 0.0
    assert result["area_code_surcharge"] == 0.0


def test_surcharge_breakdown_zero_for_freemium(mock_db_session):
    """Verify surcharge breakdown is zero for freemium users."""
    mock_user = Mock()
    mock_user.subscription_tier = "freemium"
    mock_user.id = "test_user"

    mock_db_session.query.return_value.filter.return_value.first.return_value = (
        mock_user
    )

    with patch(
        "app.services.pricing_calculator.TierConfig.get_tier_config"
    ) as mock_tier:
        mock_tier.return_value = {
            "base_sms_cost": 2.22,
            "overage_rate": 2.22,
        }

        with patch(
            "app.services.pricing_calculator.QuotaService.calculate_overage"
        ) as mock_quota:
            mock_quota.return_value = 0.0

            result = PricingCalculator.calculate_sms_cost(
                db=mock_db_session, user_id="test_user", filters={}
            )

    assert "carrier_surcharge" in result
    assert "area_code_surcharge" in result
    assert result["carrier_surcharge"] == 0.0
    assert result["area_code_surcharge"] == 0.0


@pytest.fixture
def mock_db_session():
    """Create a mock database session."""
    return MagicMock()
