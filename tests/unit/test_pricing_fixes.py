"""Test pricing calculator — v5.0 clean pricing model."""

from unittest.mock import MagicMock, patch

import pytest

from app.services.pricing_calculator import PricingCalculator


@pytest.fixture
def mock_db_session():
    return MagicMock()


def _make_user(tier="payg"):
    user = MagicMock()
    user.subscription_tier = tier
    user.id = "test_user"
    user.credits = 50.0
    return user


def test_calculate_sms_cost_requires_provider_price(mock_db_session):
    """v5.0: provider_price is required — raises if missing."""
    mock_db_session.query.return_value.filter.return_value.first.return_value = (
        _make_user()
    )
    with pytest.raises(ValueError, match="provider price unavailable"):
        PricingCalculator.calculate_sms_cost(
            db=mock_db_session, user_id="test_user", filters={}
        )


def test_calculate_sms_cost_payg_with_provider_price(mock_db_session):
    """v5.0: cost = provider_price * markup."""
    mock_db_session.query.return_value.filter.return_value.first.return_value = (
        _make_user("payg")
    )
    with patch(
        "app.services.pricing_calculator.QuotaService.calculate_overage",
        return_value=0.0,
    ):
        with patch("app.services.pricing_calculator.PricingTemplateService"):
            result = PricingCalculator.calculate_sms_cost(
                db=mock_db_session,
                user_id="test_user",
                filters={},
                provider_price=2.00,
            )
    assert result["provider_cost"] == 2.00
    assert result["base_cost"] > 0
    assert result["total_cost"] >= result["base_cost"]


def test_calculate_sms_cost_freemium_blocks_filters(mock_db_session):
    """Freemium tier cannot use filters."""
    mock_db_session.query.return_value.filter.return_value.first.return_value = (
        _make_user("freemium")
    )
    with pytest.raises(ValueError, match="Filters not available"):
        PricingCalculator.calculate_sms_cost(
            db=mock_db_session,
            user_id="test_user",
            filters={"state": "CA"},
            provider_price=2.00,
        )


def test_calculate_sms_cost_pro_no_overage_within_quota(mock_db_session):
    """Pro within quota: overage = 0."""
    mock_db_session.query.return_value.filter.return_value.first.return_value = (
        _make_user("pro")
    )
    with patch(
        "app.services.pricing_calculator.QuotaService.calculate_overage",
        return_value=0.0,
    ):
        with patch("app.services.pricing_calculator.PricingTemplateService"):
            result = PricingCalculator.calculate_sms_cost(
                db=mock_db_session,
                user_id="test_user",
                filters={},
                provider_price=2.00,
            )
    assert result["overage_charge"] == 0.0


def test_validate_balance_sufficient(mock_db_session):
    """validate_balance returns True when credits >= cost."""
    user = _make_user("payg")
    user.credits = 10.0
    mock_db_session.query.return_value.filter.return_value.first.return_value = user
    with patch(
        "app.services.pricing_calculator.QuotaService.calculate_overage",
        return_value=0.0,
    ):
        assert (
            PricingCalculator.validate_balance(mock_db_session, "test_user", 5.0)
            is True
        )


def test_validate_balance_insufficient(mock_db_session):
    """validate_balance returns False when credits < cost."""
    user = _make_user("payg")
    user.credits = 2.0
    mock_db_session.query.return_value.filter.return_value.first.return_value = user
    with patch(
        "app.services.pricing_calculator.QuotaService.calculate_overage",
        return_value=0.0,
    ):
        assert (
            PricingCalculator.validate_balance(mock_db_session, "test_user", 5.0)
            is False
        )
