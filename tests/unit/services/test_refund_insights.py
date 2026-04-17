from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.models.purchase_outcome import PurchaseOutcome
from app.services.sms_polling_service import SMSPollingService


@pytest.mark.asyncio
async def test_handle_timeout_logs_insight():
    """Verifies that _handle_timeout logs 'sms_timeout' insight to telemetry."""
    # Mocking
    mock_db = MagicMock()
    mock_verification = MagicMock()
    mock_verification.id = "test-verif-123"
    mock_verification.status = "pending"
    mock_verification.activation_id = "act-123"
    mock_verification.provider = "textverified"

    service = SMSPollingService()
    service.textverified = AsyncMock()
    service.textverified.report_verification.return_value = True

    with patch(
        "app.services.sms_polling_service.PurchaseIntelligenceService.update_sms_received",
        new_callable=AsyncMock,
    ) as mock_update_telemetry, patch(
        "app.services.sms_polling_service.refund_policy_enforcer.enforce_single_verification",
        new_callable=AsyncMock,
    ) as mock_enforce:

        mock_enforce.return_value = {"refund_amount": 0.55}

        await service._handle_timeout(mock_verification, mock_db, reason="sms_timeout")

        # Verify telemetry was called with the correct insight
        mock_update_telemetry.assert_called_once_with(
            "test-verif-123", False, refund_reason="sms_timeout"
        )

        # Verify status update
        assert mock_verification.status == "timeout"
        mock_db.commit.assert_called()


@pytest.mark.asyncio
async def test_poll_textverified_timeout_triggers_insight():
    """Verifies that an actual poll timeout triggers the 'sms_timeout' insight."""
    mock_db = MagicMock()
    mock_verification = MagicMock()
    mock_verification.id = "test-verif-456"
    mock_verification.status = "pending"
    mock_verification.activation_id = "act-456"
    mock_verification.created_at = datetime.now(timezone.utc)
    mock_verification.service_name = "whatsapp"
    mock_verification.user_id = "user-1"

    service = SMSPollingService()
    service.textverified = AsyncMock()
    # Mock result showing failure/timeout
    service.textverified.get_verification_details.return_value = {
        "number": "1234567890",
        "id": "act-456",
    }
    service.textverified.poll_sms_standard.return_value = {"success": False}

    with patch.object(
        service, "_handle_timeout", new_callable=AsyncMock
    ) as mock_timeout:
        # We need to bypass the reloading logic in the service
        with patch("app.core.database.SessionLocal", return_value=mock_db), patch(
            "app.models.Verification", return_value=mock_verification
        ):

            # Since the service re-queries the DB, we mock the query
            mock_db.query.return_value.filter.return_value.first.return_value = (
                mock_verification
            )

            await service._poll_textverified(
                mock_verification, mock_db, timeout_seconds=10
            )

            # Verify it hit _handle_timeout with the correct reason
            mock_timeout.assert_called_once()
            args, kwargs = mock_timeout.call_args
            assert kwargs["reason"] == "sms_timeout"
