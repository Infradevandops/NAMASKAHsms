"""Test area code retry logic for v4.4.1."""

from unittest.mock import AsyncMock, Mock, patch

import pytest

from app.services.textverified_service import TextVerifiedService


@pytest.mark.asyncio
async def test_cancel_safe_handles_success():
    """Verify _cancel_safe returns True on success."""
    tv = TextVerifiedService()

    if not tv.enabled:
        pytest.skip("TextVerified not configured")

    mock_client = Mock()
    mock_client.verifications.cancel = Mock()
    tv.client = mock_client

    with patch("asyncio.to_thread", new_callable=AsyncMock) as mock_thread:
        mock_thread.return_value = None
        result = await tv._cancel_safe("test_id")

    assert result is True


@pytest.mark.asyncio
async def test_cancel_safe_handles_exception():
    """Verify _cancel_safe returns False on exception and doesn't raise."""
    tv = TextVerifiedService()

    if not tv.enabled:
        pytest.skip("TextVerified not configured")

    mock_client = Mock()
    mock_client.verifications.cancel = Mock(side_effect=Exception("API error"))
    tv.client = mock_client

    with patch("asyncio.to_thread", new_callable=AsyncMock) as mock_thread:
        mock_thread.side_effect = Exception("API error")
        result = await tv._cancel_safe("test_id")

    assert result is False  # Should return False, not raise


@pytest.mark.asyncio
async def test_area_code_match_first_attempt():
    """Verify no retry when area code matches on first attempt."""
    tv = TextVerifiedService()

    if not tv.enabled:
        pytest.skip("TextVerified not configured")

    # Mock result with matching area code
    mock_result = Mock()
    mock_result.id = "test_id"
    mock_result.number = "+12125551234"  # 212 area code
    mock_result.total_cost = 2.50

    with patch("asyncio.to_thread", new_callable=AsyncMock) as mock_thread:
        mock_thread.return_value = mock_result

        result = await tv.create_verification(
            service="whatsapp",
            area_code="212",
        )

    assert result["retry_attempts"] == 0
    assert result["area_code_matched"] is True
    assert result["phone_number"] == "+12125551234"


@pytest.mark.asyncio
async def test_area_code_mismatch_triggers_retry():
    """Verify retry when area code doesn't match."""
    tv = TextVerifiedService()

    if not tv.enabled:
        pytest.skip("TextVerified not configured")

    # First attempt: wrong area code (713 - Houston)
    mock_result_1 = Mock()
    mock_result_1.id = "test_id_1"
    mock_result_1.number = "+17135551234"
    mock_result_1.total_cost = 2.50

    # Second attempt: correct area code (212 - NYC)
    mock_result_2 = Mock()
    mock_result_2.id = "test_id_2"
    mock_result_2.number = "+12125551234"
    mock_result_2.total_cost = 2.50

    call_count = 0

    def mock_create(*args, **kwargs):
        nonlocal call_count
        call_count += 1
        return mock_result_1 if call_count == 1 else mock_result_2

    with patch("asyncio.to_thread", new_callable=AsyncMock) as mock_thread:
        mock_thread.side_effect = mock_create

        with patch.object(tv, "_cancel_safe", new_callable=AsyncMock) as mock_cancel:
            mock_cancel.return_value = True

            result = await tv.create_verification(
                service="whatsapp",
                area_code="212",
            )

    assert result["retry_attempts"] == 1
    assert result["area_code_matched"] is True
    assert result["phone_number"] == "+12125551234"
    assert mock_cancel.call_count == 1  # Cancelled first attempt


@pytest.mark.asyncio
async def test_accepts_after_max_retries():
    """Verify final attempt is accepted regardless of match."""
    tv = TextVerifiedService()

    if not tv.enabled:
        pytest.skip("TextVerified not configured")

    # All attempts return wrong area code
    mock_result = Mock()
    mock_result.id = "test_id"
    mock_result.number = "+17135551234"  # 713 (Houston)
    mock_result.total_cost = 2.50

    with patch("asyncio.to_thread", new_callable=AsyncMock) as mock_thread:
        mock_thread.return_value = mock_result

        with patch.object(tv, "_cancel_safe", new_callable=AsyncMock) as mock_cancel:
            mock_cancel.return_value = True

            result = await tv.create_verification(
                service="whatsapp",
                area_code="212",
                max_retries=3,
            )

    assert result["retry_attempts"] == 2  # 0, 1, 2 (3 total attempts)
    assert result["area_code_matched"] is False
    assert result["phone_number"] == "+17135551234"  # Accepted wrong code
    assert mock_cancel.call_count == 2  # Cancelled first 2 attempts


@pytest.mark.asyncio
async def test_no_retry_when_no_area_code_requested():
    """Verify no retry loop when area code not requested."""
    tv = TextVerifiedService()

    if not tv.enabled:
        pytest.skip("TextVerified not configured")

    mock_result = Mock()
    mock_result.id = "test_id"
    mock_result.number = "+17135551234"
    mock_result.total_cost = 2.50

    with patch("asyncio.to_thread", new_callable=AsyncMock) as mock_thread:
        mock_thread.return_value = mock_result

        result = await tv.create_verification(
            service="whatsapp",
            area_code=None,  # No area code requested
        )

    assert result["retry_attempts"] == 0
    assert result["area_code_matched"] is True  # Default to True when not requested


@pytest.mark.asyncio
async def test_cancel_failure_doesnt_block_retry():
    """Verify retry continues even if cancel fails."""
    tv = TextVerifiedService()

    if not tv.enabled:
        pytest.skip("TextVerified not configured")

    mock_result_1 = Mock()
    mock_result_1.id = "test_id_1"
    mock_result_1.number = "+17135551234"
    mock_result_1.total_cost = 2.50

    mock_result_2 = Mock()
    mock_result_2.id = "test_id_2"
    mock_result_2.number = "+12125551234"
    mock_result_2.total_cost = 2.50

    call_count = 0

    def mock_create(*args, **kwargs):
        nonlocal call_count
        call_count += 1
        return mock_result_1 if call_count == 1 else mock_result_2

    with patch("asyncio.to_thread", new_callable=AsyncMock) as mock_thread:
        mock_thread.side_effect = mock_create

        with patch.object(tv, "_cancel_safe", new_callable=AsyncMock) as mock_cancel:
            mock_cancel.return_value = False  # Cancel fails

            result = await tv.create_verification(
                service="whatsapp",
                area_code="212",
            )

    # Should still retry and succeed
    assert result["retry_attempts"] == 1
    assert result["area_code_matched"] is True


@pytest.mark.asyncio
async def test_retry_with_sleep_delay():
    """Verify retry includes sleep delay between attempts."""
    tv = TextVerifiedService()

    if not tv.enabled:
        pytest.skip("TextVerified not configured")

    mock_result = Mock()
    mock_result.id = "test_id"
    mock_result.number = "+17135551234"
    mock_result.total_cost = 2.50

    with patch("asyncio.to_thread", new_callable=AsyncMock) as mock_thread:
        mock_thread.return_value = mock_result

        with patch.object(tv, "_cancel_safe", new_callable=AsyncMock) as mock_cancel:
            mock_cancel.return_value = True

            with patch("asyncio.sleep", new_callable=AsyncMock) as mock_sleep:
                result = await tv.create_verification(
                    service="whatsapp",
                    area_code="212",
                    max_retries=2,
                )

                # Should sleep once (after first failed attempt)
                assert mock_sleep.call_count == 1
                mock_sleep.assert_called_with(0.5)
