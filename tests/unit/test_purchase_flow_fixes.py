"""Tests for purchase flow fixes (Task 2)."""

from unittest.mock import MagicMock, patch

import pytest


@pytest.mark.asyncio
async def test_polling_marks_failed_when_no_activation_id():
    """Verification with no activation_id is marked failed, not silently skipped."""
    from app.services.sms_polling_service import SMSPollingService

    svc = SMSPollingService()

    mock_verification = MagicMock()
    mock_verification.id = "test-id-123"
    mock_verification.status = "pending"
    mock_verification.activation_id = None  # no activation_id
    mock_verification.failure_reason = None

    mock_db = MagicMock()
    mock_db.query.return_value.filter.return_value.first.return_value = (
        mock_verification
    )

    with patch("app.services.sms_polling_service.SessionLocal", return_value=mock_db):
        await svc._poll_verification("test-id-123")

    assert mock_verification.status == "failed"
    assert mock_verification.failure_reason == "no_activation_id"
    mock_db.commit.assert_called_once()


@pytest.mark.asyncio
async def test_polling_stops_when_not_pending():
    """Polling stops immediately if verification is not pending."""
    from app.services.sms_polling_service import SMSPollingService

    svc = SMSPollingService()

    mock_verification = MagicMock()
    mock_verification.status = "completed"
    mock_verification.activation_id = "tv_123"

    mock_db = MagicMock()
    mock_db.query.return_value.filter.return_value.first.return_value = (
        mock_verification
    )

    with patch("app.services.sms_polling_service.SessionLocal", return_value=mock_db):
        await svc._poll_verification("test-id-456")

    # Should not commit anything — just return
    mock_db.commit.assert_not_called()


@pytest.mark.asyncio
async def test_polling_stops_when_verification_not_found():
    """Polling stops gracefully when verification doesn't exist in DB."""
    from app.services.sms_polling_service import SMSPollingService

    svc = SMSPollingService()

    mock_db = MagicMock()
    mock_db.query.return_value.filter.return_value.first.return_value = None

    with patch("app.services.sms_polling_service.SessionLocal", return_value=mock_db):
        await svc._poll_verification("nonexistent-id")

    mock_db.commit.assert_not_called()


def test_stock_map_available_services_are_selectable():
    """Services with price > 0 must have available=True in stock map output."""
    import asyncio
    from unittest.mock import AsyncMock, patch

    services = [
        {"id": "tinder", "price": 0.50, "quantity": None},
        {"id": "discord", "price": 0.50, "quantity": None},
        {"id": "snapchat", "price": 0.25, "quantity": None},
    ]

    async def run():
        from app.services.stock_monitor import build_stock_map

        with patch("app.services.stock_monitor.cache") as mc, patch(
            "app.services.stock_monitor.get_purchase_outcome", return_value=None
        ):
            mc.get = AsyncMock(return_value=services)
            return await build_stock_map()

    result = asyncio.run(run())
    for slug in ["tinder", "discord", "snapchat"]:
        assert result[slug]["available"] is True, f"{slug} should be available"
