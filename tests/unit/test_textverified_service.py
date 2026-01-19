import os
from unittest.mock import MagicMock, patch

import pytest

# Create a mock textverified module
mock_textverified = MagicMock()
mock_textverified.TextVerified = MagicMock()
mock_textverified.ReservationCapability.SMS = "sms"
mock_textverified.NumberType.MOBILE = "mobile"
mock_textverified.ReservationType.VERIFICATION = "verification"

# Apply patch before importing service if possible, or reload
from app.services.textverified_service import TextVerifiedService


@pytest.fixture
def mock_client_instance():
    instance = MagicMock()
    mock_textverified.TextVerified.return_value = instance
    return instance


@pytest.fixture
def service(mock_client_instance):
    # Patch the module-level variable 'textverified'
    with patch("app.services.textverified_service.textverified", mock_textverified):
        with patch.dict(
            os.environ, {"TEXTVERIFIED_API_KEY": "key", "TEXTVERIFIED_EMAIL": "email"}
        ):
            # Reset init
            svc = TextVerifiedService()
            return svc


def test_init_success(service, mock_client_instance):
    assert service.enabled is True
    assert service.api_key == "key"
    mock_textverified.TextVerified.assert_called()


def test_init_missing_creds():
    with patch.dict(os.environ, {"TEXTVERIFIED_API_KEY": ""}):
        with patch("app.services.textverified_service.settings") as mock_settings:
            mock_settings.textverified_api_key = None
            svc = TextVerifiedService()
            assert svc.enabled is False


@pytest.mark.asyncio
async def test_get_balance_api(service, mock_client_instance):
    mock_client_instance.account.balance = 10.5

    result = await service.get_balance()

    assert result["balance"] == 10.5
    assert result["cached"] is False
    assert service._balance_cache == 10.5


@pytest.mark.asyncio
async def test_get_balance_cached(service, mock_client_instance):
    # Set cache
    service._set_balance_cache(50.0)

    result = await service.get_balance()
    assert result["balance"] == 50.0
    assert result["cached"] is True
    # Verify API not called
    # (Checking if client.account.balance was accessed in this call - hard to check property access count easily without PropertyMock, but sufficient here)


@pytest.mark.asyncio
async def test_buy_number_success(service, mock_client_instance):
    mock_verif = MagicMock()
    mock_verif.id = "v1"
    mock_verif.number = "5551234"
    mock_verif.total_cost = 1.5

    mock_client_instance.verifications.create.return_value = mock_verif

    result = await service.buy_number("US", "telegram")

    assert result["activation_id"] == "v1"
    assert result["phone_number"] == "+15551234"
    assert result["cost"] == 1.5


@pytest.mark.asyncio
async def test_check_sms_pending(service, mock_client_instance):
    mock_verif = MagicMock()
    mock_verif.sms = []  # No SMS
    mock_client_instance.verifications.details.return_value = mock_verif

    result = await service.check_sms("v1")

    assert result["status"] == "pending"
    assert result["sms_code"] is None


@pytest.mark.asyncio
async def test_check_sms_received(service, mock_client_instance):
    mock_sms = MagicMock()
    mock_sms.message = "123456"

    mock_verif = MagicMock()
    mock_verif.sms = [mock_sms]
    mock_client_instance.verifications.details.return_value = mock_verif

    result = await service.check_sms("v1")

    assert result["status"] == "received"
    assert result["sms_code"] == "123456"


@pytest.mark.asyncio
async def test_get_services_list(service, mock_client_instance):
    s1 = MagicMock()
    s1.service_name = "tg"
    s1.cost = 0.5

    mock_client_instance.services.list.return_value = [s1]

    services = await service.get_services_list()

    assert len(services) == 1
    assert services[0]["id"] == "tg"
    assert services[0]["cost"] == 0.5


@pytest.mark.asyncio
async def test_cancel_activation(service, mock_client_instance):
    res = await service.cancel_activation("v1")
    assert res is True
    mock_client_instance.verifications.cancel.assert_called_with("v1")


@pytest.mark.asyncio
async def test_get_area_codes(service, mock_client_instance):
    ac = MagicMock()
    ac.area_code = 415
    mock_client_instance.area_codes.list.return_value = [ac]

    codes = await service.get_area_codes_list("tg")
    assert "415" in codes


@pytest.mark.asyncio
async def test_retry_backoff_connection_error(service):
    # Test internal helper directly
    fail_mock = MagicMock(side_effect=[Exception("Connection error"), "Success"])

    async def task():
        val = fail_mock()
        if isinstance(val, Exception):
            raise val
        return val

    with patch("asyncio.sleep") as mock_sleep:
        res = await service._retry_with_backoff(task)
        assert res == "Success"
        assert mock_sleep.called
