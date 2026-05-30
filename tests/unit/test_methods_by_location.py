from unittest.mock import MagicMock, patch

import pytest

from app.api.billing.payment_method_endpoints import get_payment_methods_by_location


@pytest.mark.asyncio
@patch("app.api.billing.payment_method_endpoints.geolocation_service.detect_country")
async def test_methods_by_location_nigeria(mock_detect):
    mock_detect.return_value = "NG"
    mock_request = MagicMock()

    response = await get_payment_methods_by_location(
        request=mock_request, user_id="test"
    )

    assert response["country"] == "NG"
    assert len(response["recommended_methods"]) == 3
    assert response["recommended_methods"][0]["id"] == "paystack"
    assert response["recommended_methods"][1]["id"] == "local_bank_transfer"


@pytest.mark.asyncio
@patch("app.api.billing.payment_method_endpoints.geolocation_service.detect_country")
async def test_methods_by_location_india(mock_detect):
    mock_detect.return_value = "IN"
    mock_request = MagicMock()

    response = await get_payment_methods_by_location(
        request=mock_request, user_id="test"
    )

    assert response["country"] == "IN"
    assert response["recommended_methods"][0]["id"] == "upi"


@pytest.mark.asyncio
@patch("app.api.billing.payment_method_endpoints.geolocation_service.detect_country")
async def test_methods_by_location_default(mock_detect):
    mock_detect.return_value = "UNKNOWN"
    mock_request = MagicMock()

    response = await get_payment_methods_by_location(
        request=mock_request, user_id="test"
    )

    assert response["country"] == "UNKNOWN"
    assert response["recommended_methods"][0]["id"] == "stripe"
    assert response["recommended_methods"][1]["id"] == "bank_transfer"
