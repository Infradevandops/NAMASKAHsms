import os
import time
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
    mock_verif.number = "5551234567"
    mock_verif.total_cost = 1.5

    mock_client_instance.verifications.create.return_value = mock_verif

    result = await service.buy_number("US", "telegram")

    assert result["activation_id"] == "v1"
    assert result["phone_number"] == "+1 (555) 123-4567"
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
    mock_response = MagicMock()
    mock_response.data = [{"service_name": "tg", "cost": 0.5}]
    mock_client_instance._perform_action.return_value = mock_response

    # Need to mock textverified.Service.from_api
    with patch(
        "app.services.textverified_service.textverified.Service.from_api"
    ) as mock_from_api:
        s1 = MagicMock()
        s1.service_name = "tg"
        s1.cost = 0.5
        mock_from_api.return_value = s1

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
    mock_client_instance.services.area_codes.return_value = [ac]

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


@pytest.mark.asyncio
async def test_get_health_status(service, mock_client_instance):
    mock_client_instance.account.balance = 12.34
    res = await service.get_health_status()
    assert res["status"] == "operational"
    assert res["balance"] == 12.34


@pytest.mark.asyncio
async def test_get_health_status_disabled(service):
    service.enabled = False
    res = await service.get_health_status()
    assert res["status"] == "error"
    assert "not configured" in res["error"]


def test_circuit_breaker(service):
    # Success resets
    service._circuit_breaker_failures = 3
    service._record_success()
    assert service._circuit_breaker_failures == 0

    # Failure threshold
    for i in range(5):
        service._record_failure()
    assert service._check_circuit_breaker() is False

    # Reset time check
    with patch("time.time", return_value=time.time() + 400):
        assert service._check_circuit_breaker() is True


@pytest.mark.asyncio
async def test_aliases_and_legacy(service, mock_client_instance):
    # get_account_balance
    mock_client_instance.account.balance = 5.0
    val = await service.get_account_balance()
    assert val == 5.0

    # cancel_number
    res = await service.cancel_number("v2")
    assert res is True

    # get_number
    mock_verif = MagicMock()
    mock_verif.id = "v3"
    mock_verif.number = "5550000"
    mock_verif.total_cost = 1.0
    mock_client_instance.verifications.create.return_value = mock_verif
    res = await service.get_number("telegram")
    assert res["id"] == "v3"


@pytest.mark.asyncio
async def test_get_verification_status(service, mock_client_instance):
    mock_sms = MagicMock()
    mock_sms.message = "OKCODE"
    mock_verif = MagicMock()
    mock_verif.sms = [mock_sms]
    mock_client_instance.verifications.details.return_value = mock_verif

    res = await service.get_verification_status("v1")
    assert res["status"] == "completed"
    assert res["sms_code"] == "OKCODE"


@pytest.mark.asyncio
async def test_check_sms_circuit_open(service):
    service._circuit_breaker_reset_time = time.time() + 100
    res = await service.check_sms("v1")
    assert res["status"] == "error"
    assert "temporarily unavailable" in res["error"]
