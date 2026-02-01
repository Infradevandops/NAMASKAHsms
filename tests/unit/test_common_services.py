

# --- Error Handling Tests ---


from unittest.mock import AsyncMock, MagicMock, patch
import httpx
import pytest
from app.services.audit_service import AuditService
from app.services.error_handling import APIErrorHandler, RetryConfig, retry_with_backoff

def test_retry_config():

    config = RetryConfig(max_retries=5, initial_delay=0.1)
    assert config.max_retries == 5
    assert config.get_delay(0) == 0.1
    assert config.get_delay(1) == 0.2
    assert config.get_delay(2) == 0.4


@pytest.mark.asyncio
async def test_retry_with_backoff_success():
    mock_func = AsyncMock(return_value="success")

    @retry_with_backoff()
    async def decorated():
        return await mock_func()

    result = await decorated()
    assert result == "success"
    assert mock_func.call_count == 1


@pytest.mark.asyncio
async def test_retry_with_backoff_retries():
    # Fail twice, succeed third time
    mock_func = AsyncMock(side_effect=[httpx.HTTPError("Fail"), httpx.ReadTimeout("Timeout"), "Success"])

    @retry_with_backoff(RetryConfig(max_retries=3, initial_delay=0.01))
    async def decorated():
        return await mock_func()

    result = await decorated()
    assert result == "Success"
    assert mock_func.call_count == 3


@pytest.mark.asyncio
async def test_retry_with_backoff_fail_max():
    mock_func = AsyncMock(side_effect=httpx.HTTPError("Always fail"))

    @retry_with_backoff(RetryConfig(max_retries=2, initial_delay=0.01))
    async def decorated():
        return await mock_func()

with pytest.raises(httpx.HTTPError):
        await decorated()

    assert mock_func.call_count == 2


def test_retry_sync_wrapper():

    mock_func = MagicMock(side_effect=[Exception("Sync fail"), "Success"])

    @retry_with_backoff(RetryConfig(max_retries=2, initial_delay=0.01))
def decorated():

        return mock_func()

    # Need to patch asyncio.run and sleep to avoid actual waiting/context issues in sync test if logic uses asyncio.run
    # The implementation uses asyncio.run(asyncio.sleep(delay))
with patch("asyncio.run"), patch("asyncio.sleep"):
        result = decorated()
        assert result == "Success"
        assert mock_func.call_count == 2


def test_api_error_handler():

    assert APIErrorHandler.get_user_message(404) == "Resource not found."
    assert APIErrorHandler.get_user_message(404, "Details") == "Resource not found. (Details)"
    assert APIErrorHandler.get_user_message(999) == "An error occurred. Please try again."

    assert APIErrorHandler.is_retryable(503) is True
    assert APIErrorHandler.is_retryable(404) is False


def test_api_error_handler_log():

with patch("app.services.error_handling.logger.error") as mock_log:
        APIErrorHandler.log_error("TestError", 500, "Msg", {"id": 1})
        mock_log.assert_called_once()
        args = mock_log.call_args[0][0]
        assert "TestError" in args
        assert "Msg" in args
        assert "'id': 1" in args


# --- Audit Service Tests ---


@pytest.fixture
def audit_service():

    return AuditService()


@pytest.mark.asyncio
async def test_audit_log_flow(audit_service):
    # Log action
    await audit_service.log_action("user1", "login", "auth", {"ip": "1.2.3.4"})

    assert len(audit_service.audit_log) == 1
    entry = audit_service.audit_log[0]
    assert entry["user_id"] == "user1"
    assert entry["action"] == "login"

    # Get log
    logs = await audit_service.get_user_audit_log("user1")
    assert len(logs) == 1

    logs_other = await audit_service.get_user_audit_log("user2")
    assert len(logs_other) == 0


@pytest.mark.asyncio
async def test_audit_export_delete(audit_service):
    await audit_service.log_action("user1", "read", "doc")

    export = await audit_service.export_audit_log("user1")
    assert export["user_id"] == "user1"
    assert len(export["audit_log"]) == 1

    await audit_service.delete_user_data("user1")
    assert len(audit_service.audit_log) == 0