"""Unit tests for SMS polling provider dispatch — Issue 4 from STABILITY_CHECKLIST.md."""

import pytest
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

from app.services.sms_polling_service import SMSPollingService
from app.services.providers.base_provider import MessageResult


def _make_verification(provider="textverified", status="pending"):
    v = MagicMock()
    v.id = "verif-1"
    v.activation_id = "act-123"
    v.provider = provider
    v.status = status
    v.user_id = "user-1"
    v.service_name = "whatsapp"
    v.phone_number = "+12025551234"
    v.created_at = datetime(2026, 3, 26, 12, 0, 0, tzinfo=timezone.utc)
    v.ends_at = None
    return v


@pytest.fixture
def service():
    with patch("app.services.sms_polling_service.TextVerifiedService"):
        return SMSPollingService()


# ── dispatch by provider ──────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_poll_verification_dispatches_textverified(service):
    v = _make_verification(provider="textverified")

    with patch.object(
        service, "_poll_textverified", new_callable=AsyncMock
    ) as mock_tv, patch("app.services.sms_polling_service.SessionLocal") as mock_db:
        mock_db.return_value.__enter__ = MagicMock(return_value=MagicMock())
        mock_db.return_value.__exit__ = MagicMock(return_value=False)
        db = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = v
        mock_db.return_value = db

        await service._poll_verification("verif-1")

    mock_tv.assert_called_once()


@pytest.mark.asyncio
async def test_poll_verification_dispatches_telnyx(service):
    v = _make_verification(provider="telnyx")

    with patch.object(
        service, "_poll_telnyx", new_callable=AsyncMock
    ) as mock_telnyx, patch("app.services.sms_polling_service.SessionLocal") as mock_db:
        db = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = v
        mock_db.return_value = db

        await service._poll_verification("verif-1")

    mock_telnyx.assert_called_once()


@pytest.mark.asyncio
async def test_poll_verification_dispatches_fivesim(service):
    v = _make_verification(provider="5sim")

    with patch.object(
        service, "_poll_fivesim", new_callable=AsyncMock
    ) as mock_5sim, patch("app.services.sms_polling_service.SessionLocal") as mock_db:
        db = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = v
        mock_db.return_value = db

        await service._poll_verification("verif-1")

    mock_5sim.assert_called_once()


@pytest.mark.asyncio
async def test_poll_verification_unknown_provider(service):
    v = _make_verification(provider="unknown_provider")

    with patch.object(
        service, "_handle_timeout", new_callable=AsyncMock
    ) as mock_timeout, patch(
        "app.services.sms_polling_service.SessionLocal"
    ) as mock_db:
        db = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = v
        mock_db.return_value = db

        await service._poll_verification("verif-1")

    mock_timeout.assert_called_once()


# ── _poll_telnyx ──────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_poll_telnyx_success(service):
    v = _make_verification(provider="telnyx")
    db = MagicMock()
    msg = MessageResult(
        text="Code 123456", code="123456", received_at="2026-03-26T12:00:00Z"
    )

    with patch("app.services.sms_polling_service.TelnyxAdapter") as MockAdapter:
        adapter = AsyncMock()
        adapter.check_messages = AsyncMock(return_value=[msg])
        MockAdapter.return_value = adapter

        with patch("app.services.sms_polling_service.NotificationDispatcher"):
            await service._poll_telnyx(v, db, timeout_seconds=30)

    assert v.status == "completed"
    assert v.sms_code == "123456"
    db.commit.assert_called()


@pytest.mark.asyncio
async def test_poll_telnyx_timeout(service):
    v = _make_verification(provider="telnyx")
    db = MagicMock()

    with patch(
        "app.services.sms_polling_service.TelnyxAdapter"
    ) as MockAdapter, patch.object(
        service, "_handle_timeout", new_callable=AsyncMock
    ) as mock_timeout:
        adapter = AsyncMock()
        adapter.check_messages = AsyncMock(return_value=[])
        MockAdapter.return_value = adapter

        # Very short timeout so loop exits immediately
        await service._poll_telnyx(v, db, timeout_seconds=0)

    mock_timeout.assert_called_once_with(v, db)


@pytest.mark.asyncio
async def test_poll_telnyx_api_error(service):
    v = _make_verification(provider="telnyx")
    db = MagicMock()

    with patch(
        "app.services.sms_polling_service.TelnyxAdapter"
    ) as MockAdapter, patch.object(
        service, "_handle_timeout", new_callable=AsyncMock
    ) as mock_timeout:
        adapter = AsyncMock()
        adapter.check_messages = AsyncMock(side_effect=Exception("API error"))
        MockAdapter.return_value = adapter

        await service._poll_telnyx(v, db, timeout_seconds=0)

    mock_timeout.assert_called_once()


# ── _poll_fivesim ─────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_poll_fivesim_success(service):
    v = _make_verification(provider="5sim")
    db = MagicMock()
    msg = MessageResult(
        text="Code 654321", code="654321", received_at="2026-03-26T12:00:00Z"
    )

    with patch("app.services.sms_polling_service.FiveSimAdapter") as MockAdapter:
        adapter = AsyncMock()
        adapter.check_messages = AsyncMock(return_value=[msg])
        MockAdapter.return_value = adapter

        with patch("app.services.sms_polling_service.NotificationDispatcher"):
            await service._poll_fivesim(v, db, timeout_seconds=30)

    assert v.status == "completed"
    assert v.sms_code == "654321"
    db.commit.assert_called()


@pytest.mark.asyncio
async def test_poll_fivesim_timeout(service):
    v = _make_verification(provider="5sim")
    db = MagicMock()

    with patch(
        "app.services.sms_polling_service.FiveSimAdapter"
    ) as MockAdapter, patch.object(
        service, "_handle_timeout", new_callable=AsyncMock
    ) as mock_timeout:
        adapter = AsyncMock()
        adapter.check_messages = AsyncMock(return_value=[])
        MockAdapter.return_value = adapter

        await service._poll_fivesim(v, db, timeout_seconds=0)

    mock_timeout.assert_called_once_with(v, db)


@pytest.mark.asyncio
async def test_poll_fivesim_api_error(service):
    v = _make_verification(provider="5sim")
    db = MagicMock()

    with patch(
        "app.services.sms_polling_service.FiveSimAdapter"
    ) as MockAdapter, patch.object(
        service, "_handle_timeout", new_callable=AsyncMock
    ) as mock_timeout:
        adapter = AsyncMock()
        adapter.check_messages = AsyncMock(side_effect=Exception("API error"))
        MockAdapter.return_value = adapter

        await service._poll_fivesim(v, db, timeout_seconds=0)

    mock_timeout.assert_called_once()


# ── _handle_timeout provider dispatch ────────────────────────────────────────


@pytest.mark.asyncio
async def test_handle_timeout_textverified(service):
    v = _make_verification(provider="textverified")
    db = MagicMock()
    service.textverified.report_verification = AsyncMock(return_value=True)

    with patch("app.services.sms_polling_service.NotificationService"):
        await service._handle_timeout(v, db)

    service.textverified.report_verification.assert_called_once_with("act-123")
    assert v.status == "timeout"


@pytest.mark.asyncio
async def test_handle_timeout_telnyx(service):
    v = _make_verification(provider="telnyx")
    db = MagicMock()

    with patch("app.services.sms_polling_service.TelnyxAdapter") as MockAdapter, patch(
        "app.services.sms_polling_service.NotificationService"
    ):
        adapter = AsyncMock()
        adapter.report_failed = AsyncMock(return_value=True)
        MockAdapter.return_value = adapter

        await service._handle_timeout(v, db)

    adapter.report_failed.assert_called_once_with("act-123")
    assert v.status == "timeout"


@pytest.mark.asyncio
async def test_handle_timeout_fivesim(service):
    v = _make_verification(provider="5sim")
    db = MagicMock()

    with patch("app.services.sms_polling_service.FiveSimAdapter") as MockAdapter, patch(
        "app.services.sms_polling_service.NotificationService"
    ):
        adapter = AsyncMock()
        adapter.report_failed = AsyncMock(return_value=True)
        MockAdapter.return_value = adapter

        await service._handle_timeout(v, db)

    adapter.report_failed.assert_called_once_with("act-123")
    assert v.status == "timeout"


@pytest.mark.asyncio
async def test_handle_timeout_refund_fallback(service):
    """When provider report fails, platform refund kicks in."""
    v = _make_verification(provider="textverified")
    db = MagicMock()
    service.textverified.report_verification = AsyncMock(return_value=False)

    with patch(
        "app.services.sms_polling_service.AutoRefundService"
    ) as MockRefund, patch("app.services.sms_polling_service.NotificationService"):
        refund_svc = AsyncMock()
        refund_svc.process_verification_refund = AsyncMock(
            return_value={"refund_amount": 2.22}
        )
        MockRefund.return_value = refund_svc

        await service._handle_timeout(v, db)

    refund_svc.process_verification_refund.assert_called_once()


# ── background service ────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_background_service_polls_all_providers(service):
    """Background service picks up pending verifications from all providers."""
    tv_v = _make_verification(provider="textverified")
    tv_v.id = "v1"
    telnyx_v = _make_verification(provider="telnyx")
    telnyx_v.id = "v2"
    fivesim_v = _make_verification(provider="5sim")
    fivesim_v.id = "v3"

    service.is_running = True
    call_count = 0

    async def stop_after_one(*args, **kwargs):
        nonlocal call_count
        call_count += 1
        service.is_running = False

    with patch(
        "app.services.sms_polling_service.SessionLocal"
    ) as mock_db, patch.object(
        service, "start_polling", new_callable=AsyncMock
    ) as mock_start, patch(
        "asyncio.sleep", new_callable=AsyncMock, side_effect=stop_after_one
    ):
        db = MagicMock()
        db.query.return_value.filter.return_value.all.return_value = [
            tv_v,
            telnyx_v,
            fivesim_v,
        ]
        mock_db.return_value = db

        await service.start_background_service()

    assert mock_start.call_count == 3
