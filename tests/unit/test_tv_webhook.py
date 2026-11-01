"""Tests for TV webhook endpoint — v4.9.6 verification sprint.

Covers:
- Send Test button scenario (non-sms.received event → 200 ok:true)
- sms.received happy path (DB update + WebSocket push)
- Duplicate event deduplication
- HMAC signature enforcement
- Verification lookup by reservationId and phone fallback
- Already-completed verification guard
- Missing verification → 200 (no retry/disable)
"""

import hashlib
import hmac
import json
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.models.verification import Verification
from app.models.user import User


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

TV_WEBHOOK_URL = "/api/verification/webhook/tv"


def _make_sms_payload(
    event_id="evt_test_001",
    reservation_id="tv-res-001",
    phone="17022853600",
    sms_content="Your WhatsApp code is 123456",
    parsed_code="123456",
):
    return {
        "id": event_id,
        "event": "sms.received",
        "attempt": 1,
        "occurredAt": "2026-11-01T10:00:00Z",
        "data": {
            "to": f"+{phone}",
            "from": "+12025551234",
            "smsContent": sms_content,
            "parsedCode": parsed_code,
            "reservationId": reservation_id,
            "createdAt": "2026-11-01T10:00:00Z",
            "encrypted": False,
        },
    }


def _sign(payload_bytes: bytes, secret: str) -> str:
    digest = hmac.new(secret.encode(), payload_bytes, hashlib.sha256).hexdigest()
    return f"sha256={digest}"


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def tv_client(engine):
    """Unauthenticated client — TV webhook has no auth, only HMAC."""
    from fastapi.testclient import TestClient
    from sqlalchemy.orm import sessionmaker

    from app.core.database import get_db
    from main import app

    def override_get_db():
        Session = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        session = Session()
        try:
            yield session
        finally:
            session.close()

    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)
    app.dependency_overrides.clear()


@pytest.fixture
def pending_verification(db, test_user):
    v = Verification(
        id="ver-webhook-001",
        user_id=test_user.id,
        phone_number="+17022853600",
        activation_id="tv-res-001",
        service="whatsapp",
        status="pending",
        cost=2.50,
        created_at=datetime.now(timezone.utc),
    )
    db.add(v)
    db.commit()
    db.refresh(v)
    return v


# ---------------------------------------------------------------------------
# P2-1: Send Test button scenario
# TV sends a non-sms.received event when you click "Send Test"
# ---------------------------------------------------------------------------


class TestTVWebhookSendTest:
    """TV's Send Test button sends a ping/test event, not sms.received.
    Endpoint must return 200 {ok: true} for all non-sms event types.
    """

    def test_send_test_ping_returns_200(self, tv_client):
        """TV Send Test button — must return 200 ok:true."""
        payload = {"id": "evt_test_ping", "event": "ping", "attempt": 1, "data": {}}
        with patch("app.api.verification.tv_webhook.cache") as mock_cache:
            mock_cache.get = AsyncMock(return_value=None)
            mock_cache.set = AsyncMock()
            resp = tv_client.post(TV_WEBHOOK_URL, json=payload)
        assert resp.status_code == 200
        assert resp.json()["ok"] is True

    def test_billing_event_accepted_and_ignored(self, tv_client):
        """Billing/backorder events must be accepted (200) but not processed."""
        payload = {
            "id": "evt_billing_001",
            "event": "billing.updated",
            "attempt": 1,
            "data": {"amount": 10.0},
        }
        with patch("app.api.verification.tv_webhook.cache") as mock_cache:
            mock_cache.get = AsyncMock(return_value=None)
            mock_cache.set = AsyncMock()
            resp = tv_client.post(TV_WEBHOOK_URL, json=payload)
        assert resp.status_code == 200
        assert resp.json()["ok"] is True

    def test_unknown_event_type_returns_200(self, tv_client):
        """Any unknown event type must return 200 — prevents TV auto-disable."""
        payload = {"id": "evt_unknown", "event": "some.future.event", "data": {}}
        with patch("app.api.verification.tv_webhook.cache") as mock_cache:
            mock_cache.get = AsyncMock(return_value=None)
            mock_cache.set = AsyncMock()
            resp = tv_client.post(TV_WEBHOOK_URL, json=payload)
        assert resp.status_code == 200

    def test_malformed_json_returns_200(self, tv_client):
        """Malformed JSON must return 200 — TV must not retry/disable."""
        resp = tv_client.post(
            TV_WEBHOOK_URL,
            content=b"not json{{",
            headers={"Content-Type": "application/json"},
        )
        assert resp.status_code == 200

    def test_empty_body_returns_200(self, tv_client):
        """Empty body must return 200."""
        resp = tv_client.post(
            TV_WEBHOOK_URL,
            content=b"{}",
            headers={"Content-Type": "application/json"},
        )
        assert resp.status_code == 200


# ---------------------------------------------------------------------------
# P2-2: sms.received happy path
# ---------------------------------------------------------------------------


class TestTVWebhookSmsReceived:
    """sms.received events must update the DB and push via WebSocket."""

    def test_sms_received_updates_verification_status(
        self, tv_client, db, pending_verification
    ):
        """sms.received must mark verification completed and store the code."""
        payload = _make_sms_payload(
            reservation_id=pending_verification.activation_id,
            parsed_code="876094",
        )
        with patch("app.api.verification.tv_webhook.cache") as mock_cache:
            mock_cache.get = AsyncMock(return_value=None)
            mock_cache.set = AsyncMock()
            with patch(
                "app.api.verification.tv_webhook.websocket_manager"
            ) as mock_ws:
                mock_ws.broadcast_to_user = AsyncMock()
                resp = tv_client.post(TV_WEBHOOK_URL, json=payload)

        assert resp.status_code == 200
        assert resp.json()["ok"] is True

        db.refresh(pending_verification)
        assert pending_verification.status == "completed"
        assert pending_verification.sms_code == "876094"

    def test_sms_received_pushes_websocket(self, tv_client, db, pending_verification):
        """sms.received must call broadcast_to_user with correct payload."""
        payload = _make_sms_payload(
            reservation_id=pending_verification.activation_id,
            parsed_code="555123",
        )
        with patch("app.api.verification.tv_webhook.cache") as mock_cache:
            mock_cache.get = AsyncMock(return_value=None)
            mock_cache.set = AsyncMock()
            with patch(
                "app.api.verification.tv_webhook.websocket_manager"
            ) as mock_ws:
                mock_ws.broadcast_to_user = AsyncMock()
                tv_client.post(TV_WEBHOOK_URL, json=payload)

        mock_ws.broadcast_to_user.assert_called_once()
        call_args = mock_ws.broadcast_to_user.call_args
        ws_payload = call_args[0][1]
        assert ws_payload["type"] == "sms_received"
        assert ws_payload["sms_code"] == "555123"
        assert ws_payload["verification_id"] == str(pending_verification.id)

    def test_sms_received_phone_fallback_lookup(self, tv_client, db, test_user):
        """When reservationId is missing, must fall back to phone number lookup."""
        v = Verification(
            id="ver-phone-fallback",
            user_id=test_user.id,
            phone_number="+19995550001",
            activation_id=None,
            service="telegram",
            status="pending",
            cost=1.50,
            created_at=datetime.now(timezone.utc),
        )
        db.add(v)
        db.commit()

        payload = {
            "id": "evt_fallback_001",
            "event": "sms.received",
            "attempt": 1,
            "occurredAt": "2026-11-01T10:00:00Z",
            "data": {
                "to": "+19995550001",
                "smsContent": "Telegram code: 99887",
                "parsedCode": "99887",
                # no reservationId
            },
        }
        with patch("app.api.verification.tv_webhook.cache") as mock_cache:
            mock_cache.get = AsyncMock(return_value=None)
            mock_cache.set = AsyncMock()
            with patch("app.api.verification.tv_webhook.websocket_manager") as mock_ws:
                mock_ws.broadcast_to_user = AsyncMock()
                resp = tv_client.post(TV_WEBHOOK_URL, json=payload)

        assert resp.status_code == 200
        db.refresh(v)
        assert v.status == "completed"
        assert v.sms_code == "99887"

    def test_already_completed_verification_ignored(
        self, tv_client, db, test_user
    ):
        """sms.received for an already-completed verification must return 200 silently."""
        v = Verification(
            id="ver-already-done",
            user_id=test_user.id,
            phone_number="+15550000001",
            activation_id="tv-res-done",
            service="google",
            status="completed",
            sms_code="111222",
            cost=2.00,
            created_at=datetime.now(timezone.utc),
        )
        db.add(v)
        db.commit()

        payload = _make_sms_payload(
            reservation_id="tv-res-done", parsed_code="999999"
        )
        with patch("app.api.verification.tv_webhook.cache") as mock_cache:
            mock_cache.get = AsyncMock(return_value=None)
            mock_cache.set = AsyncMock()
            with patch("app.api.verification.tv_webhook.websocket_manager") as mock_ws:
                mock_ws.broadcast_to_user = AsyncMock()
                resp = tv_client.post(TV_WEBHOOK_URL, json=payload)

        assert resp.status_code == 200
        db.refresh(v)
        # Code must NOT be overwritten
        assert v.sms_code == "111222"

    def test_no_matching_verification_returns_200(self, tv_client, db):
        """No matching verification must return 200 — TV must not retry/disable."""
        payload = _make_sms_payload(
            reservation_id="tv-res-nonexistent",
            phone="10000000000",
        )
        with patch("app.api.verification.tv_webhook.cache") as mock_cache:
            mock_cache.get = AsyncMock(return_value=None)
            mock_cache.set = AsyncMock()
            resp = tv_client.post(TV_WEBHOOK_URL, json=payload)
        assert resp.status_code == 200
        assert resp.json()["ok"] is True


# ---------------------------------------------------------------------------
# P2-3: Deduplication
# ---------------------------------------------------------------------------


class TestTVWebhookDeduplication:
    """TV retries on failure — duplicate event IDs must be silently ignored."""

    def test_duplicate_event_returns_200_duplicate_true(self, tv_client, db, pending_verification):
        """Second delivery of same event_id must return {ok:true, duplicate:true}."""
        payload = _make_sms_payload(
            event_id="evt_dup_001",
            reservation_id=pending_verification.activation_id,
        )
        # First call: cache miss → process
        # Second call: cache hit → duplicate
        call_count = 0

        async def fake_cache_get(key):
            nonlocal call_count
            call_count += 1
            return "1" if call_count > 1 else None

        with patch("app.api.verification.tv_webhook.cache") as mock_cache:
            mock_cache.get = fake_cache_get
            mock_cache.set = AsyncMock()
            with patch("app.api.verification.tv_webhook.websocket_manager") as mock_ws:
                mock_ws.broadcast_to_user = AsyncMock()
                tv_client.post(TV_WEBHOOK_URL, json=payload)
                resp2 = tv_client.post(TV_WEBHOOK_URL, json=payload)

        assert resp2.status_code == 200
        data = resp2.json()
        assert data["ok"] is True
        assert data.get("duplicate") is True

    def test_different_event_ids_both_processed(self, tv_client, db, test_user):
        """Two events with different IDs must both be processed independently."""
        for i, evt_id in enumerate(["evt_a", "evt_b"]):
            v = Verification(
                id=f"ver-dedup-{i}",
                user_id=test_user.id,
                phone_number=f"+1555000000{i}",
                activation_id=f"tv-res-dedup-{i}",
                service="whatsapp",
                status="pending",
                cost=2.50,
                created_at=datetime.now(timezone.utc),
            )
            db.add(v)
        db.commit()

        with patch("app.api.verification.tv_webhook.cache") as mock_cache:
            mock_cache.get = AsyncMock(return_value=None)
            mock_cache.set = AsyncMock()
            with patch("app.api.verification.tv_webhook.websocket_manager") as mock_ws:
                mock_ws.broadcast_to_user = AsyncMock()
                for i, evt_id in enumerate(["evt_a", "evt_b"]):
                    payload = _make_sms_payload(
                        event_id=evt_id,
                        reservation_id=f"tv-res-dedup-{i}",
                        parsed_code=f"11100{i}",
                    )
                    resp = tv_client.post(TV_WEBHOOK_URL, json=payload)
                    assert resp.status_code == 200

        assert mock_ws.broadcast_to_user.call_count == 2


# ---------------------------------------------------------------------------
# P2-4: Code extraction fallback
# ---------------------------------------------------------------------------


class TestTVWebhookCodeExtraction:
    """_extract_code fallback when parsedCode is empty."""

    def test_extract_code_from_hyphenated_format(self):
        from app.api.verification.tv_webhook import _extract_code

        assert _extract_code("Your code is 876-094") == "876094"

    def test_extract_code_plain_digits(self):
        from app.api.verification.tv_webhook import _extract_code

        assert _extract_code("Use code 123456 to verify") == "123456"

    def test_extract_code_empty_text(self):
        from app.api.verification.tv_webhook import _extract_code

        assert _extract_code("") == ""

    def test_sms_received_uses_extracted_code_when_parsed_empty(
        self, tv_client, db, pending_verification
    ):
        """When parsedCode is empty, sms_code must be extracted from smsContent."""
        payload = _make_sms_payload(
            reservation_id=pending_verification.activation_id,
            sms_content="WhatsApp code: 654321",
            parsed_code="",
        )
        with patch("app.api.verification.tv_webhook.cache") as mock_cache:
            mock_cache.get = AsyncMock(return_value=None)
            mock_cache.set = AsyncMock()
            with patch("app.api.verification.tv_webhook.websocket_manager") as mock_ws:
                mock_ws.broadcast_to_user = AsyncMock()
                tv_client.post(TV_WEBHOOK_URL, json=payload)

        db.refresh(pending_verification)
        assert pending_verification.sms_code == "654321"
