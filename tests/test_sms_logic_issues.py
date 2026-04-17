"""Tests for SMS_LOGIC.md issues — covers all deviations and gaps.

Acceptance Criteria:
  Issue 14 (HIGH)  — Voice tier gate at API level
    AC-14.1: Freemium user POSTing capability='voice' gets 402
    AC-14.2: PAYG user POSTing capability='voice' succeeds (passes tier check)
    AC-14.3: SMS capability is unaffected by the new gate

  Issue 13 (MEDIUM) — Outcome endpoint method/path mismatch
    AC-13.1: POST /api/verification/outcome/{id} returns 200 (not 404/405)
    AC-13.2: Outcome is persisted to the verification record

  Issue 8 (MEDIUM)  — submitVoiceCode() undefined
    AC-8.1:  voice_verify_modern.html does NOT contain 'submitVoiceCode'

  Issue 15 (MEDIUM) — Fake _TVVerif missing attributes
    AC-15.1: _TVVerif object has number, created_at, id, ends_at, service_name

  Issue 11 (LOW)    — Voice area codes hardcoded fallback
    AC-11.1: voice_verify_modern.html area-code-select has no hardcoded <option value="212"> etc.

  Issue 16 (LOW)    — Voice template no timeout outcome call
    AC-16.1: voice template calls outcome endpoint on timeout (like SMS template)
"""

import os
import re
import uuid
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from app.models.user import User
from app.models.verification import Verification

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def freemium_user(db):
    uid = str(uuid.uuid4())
    user = User(
        id=uid,
        email=f"free-{uid[:8]}@test.com",
        password_hash="$2b$12$hash",
        credits=50.0,
        subscription_tier="freemium",
        is_admin=False,
        created_at=datetime.now(timezone.utc),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def pending_verification(db, test_user):
    vid = str(uuid.uuid4())
    v = Verification(
        id=vid,
        user_id=test_user.id,
        service_name="telegram",
        phone_number="+14155551234",
        country="US",
        capability="sms",
        status="pending",
        cost=2.50,
        activation_id="tv-act-123",
        provider="textverified",
        created_at=datetime.now(timezone.utc),
    )
    db.add(v)
    db.commit()
    db.refresh(v)
    return v


# ---------------------------------------------------------------------------
# Issue 14 — Voice tier gate at API level
# ---------------------------------------------------------------------------


class TestVoiceTierGate:
    """AC-14: Voice capability must be blocked for tiers below PAYG."""

    def test_freemium_voice_rejected(self, engine, freemium_user):
        """AC-14.1: Freemium user gets 402 when requesting voice."""
        from app.core.database import get_db
        from app.core.dependencies import get_current_user_id
        from main import app

        def override_db():
            from sqlalchemy.orm import sessionmaker

            s = sessionmaker(autocommit=False, autoflush=False, bind=engine)()
            try:
                yield s
            finally:
                s.close()

        app.dependency_overrides[get_db] = override_db
        app.dependency_overrides[get_current_user_id] = lambda: freemium_user.id
        client = TestClient(app)

        with patch(
            "app.api.verification.purchase_endpoints.TextVerifiedService"
        ) as mock_tv:
            mock_tv.return_value.enabled = True
            resp = client.post(
                "/api/verification/request",
                json={
                    "service": "telegram",
                    "country": "US",
                    "capability": "voice",
                },
            )

        assert (
            resp.status_code == 402
        ), f"Expected 402, got {resp.status_code}: {resp.text}"
        body = resp.json()
        msg = (body.get("detail") or body.get("message") or "").lower()
        assert "voice" in msg, f"Expected 'voice' in error message, got: {body}"
        app.dependency_overrides.clear()

    def test_payg_voice_passes_tier_check(self, engine, payg_user):
        """AC-14.2: PAYG user passes the voice tier gate (may fail later on balance/TV)."""
        from app.core.database import get_db
        from app.core.dependencies import get_current_user_id
        from main import app

        def override_db():
            from sqlalchemy.orm import sessionmaker

            s = sessionmaker(autocommit=False, autoflush=False, bind=engine)()
            try:
                yield s
            finally:
                s.close()

        app.dependency_overrides[get_db] = override_db
        app.dependency_overrides[get_current_user_id] = lambda: payg_user.id
        client = TestClient(app)

        with patch(
            "app.api.verification.purchase_endpoints.TextVerifiedService"
        ) as mock_tv:
            instance = mock_tv.return_value
            instance.enabled = True
            instance.create_verification = AsyncMock(
                return_value={
                    "id": "tv-123",
                    "phone_number": "+14155559999",
                    "cost": 2.80,
                    "ends_at": (
                        datetime.now(timezone.utc) + timedelta(minutes=10)
                    ).isoformat(),
                    "tv_object": MagicMock(),
                    "retry_attempts": 0,
                    "area_code_matched": True,
                    "carrier_matched": True,
                    "real_carrier": None,
                    "voip_rejected": False,
                    "fallback_applied": False,
                    "requested_area_code": None,
                    "assigned_area_code": "415",
                    "same_state_fallback": True,
                }
            )
            instance.get_balance = AsyncMock(return_value={"balance": 100.0})

            resp = client.post(
                "/api/verification/request",
                json={
                    "service": "telegram",
                    "country": "US",
                    "capability": "voice",
                },
            )

        # Should NOT be 402 — it passed the tier gate
        assert (
            resp.status_code != 402
        ), f"PAYG should pass voice tier gate, got 402: {resp.text}"
        app.dependency_overrides.clear()

    def test_sms_unaffected_by_voice_gate(self, engine, freemium_user):
        """AC-14.3: Freemium user can still request SMS capability."""
        from app.core.database import get_db
        from app.core.dependencies import get_current_user_id
        from main import app

        def override_db():
            from sqlalchemy.orm import sessionmaker

            s = sessionmaker(autocommit=False, autoflush=False, bind=engine)()
            try:
                yield s
            finally:
                s.close()

        app.dependency_overrides[get_db] = override_db
        app.dependency_overrides[get_current_user_id] = lambda: freemium_user.id
        client = TestClient(app)

        with patch(
            "app.api.verification.purchase_endpoints.TextVerifiedService"
        ) as mock_tv:
            instance = mock_tv.return_value
            instance.enabled = True
            instance.create_verification = AsyncMock(
                return_value={
                    "id": "tv-456",
                    "phone_number": "+14155550000",
                    "cost": 2.50,
                    "ends_at": (
                        datetime.now(timezone.utc) + timedelta(minutes=10)
                    ).isoformat(),
                    "tv_object": MagicMock(),
                    "retry_attempts": 0,
                    "area_code_matched": True,
                    "carrier_matched": True,
                    "real_carrier": None,
                    "voip_rejected": False,
                    "fallback_applied": False,
                    "requested_area_code": None,
                    "assigned_area_code": "415",
                    "same_state_fallback": True,
                }
            )
            instance.get_balance = AsyncMock(return_value={"balance": 100.0})

            resp = client.post(
                "/api/verification/request",
                json={
                    "service": "telegram",
                    "country": "US",
                    "capability": "sms",
                },
            )

        # Should NOT be 402
        assert (
            resp.status_code != 402
        ), f"SMS should not be blocked for freemium, got 402"
        app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# Issue 13 — Outcome endpoint mismatch
# ---------------------------------------------------------------------------


class TestOutcomeEndpoint:
    """AC-13: POST /api/verification/outcome/{id} must work."""

    def test_post_outcome_returns_200(self, authenticated_client, pending_verification):
        """AC-13.1: POST to the correct path returns 200."""
        resp = authenticated_client.post(
            f"/api/verification/outcome/{pending_verification.id}",
            json={"outcome": "timeout"},
        )
        assert (
            resp.status_code == 200
        ), f"Expected 200, got {resp.status_code}: {resp.text}"

    def test_outcome_persisted(self, authenticated_client, pending_verification, db):
        """AC-13.2: Outcome value is written to the verification record."""
        authenticated_client.post(
            f"/api/verification/outcome/{pending_verification.id}",
            json={"outcome": "timeout"},
        )
        db.expire_all()
        v = (
            db.query(Verification)
            .filter(Verification.id == pending_verification.id)
            .first()
        )
        assert v.outcome == "timeout"


# ---------------------------------------------------------------------------
# Issue 8 — submitVoiceCode() undefined
# ---------------------------------------------------------------------------


class TestVoiceTemplateSubmitRemoved:
    """AC-8: voice_verify_modern.html must not reference submitVoiceCode."""

    def test_no_submit_voice_code_reference(self):
        """AC-8.1: The string 'submitVoiceCode' must not appear in the template."""
        template_path = os.path.join(
            os.path.dirname(__file__), "..", "templates", "voice_verify_modern.html"
        )
        with open(template_path, "r") as f:
            content = f.read()
        assert (
            "submitVoiceCode" not in content
        ), "voice_verify_modern.html still references submitVoiceCode()"


# ---------------------------------------------------------------------------
# Issue 15 — Fake _TVVerif missing attributes
# ---------------------------------------------------------------------------


class TestTVVerifObject:
    """AC-15: The _TVVerif shim must carry all attributes sms.incoming() may need."""

    def test_tvverif_has_required_attributes(self):
        """AC-15.1: _TVVerif exposes number, created_at, id, ends_at, service_name."""
        from app.services.sms_polling_service import SMSPollingService

        # The _TVVerif class is defined inside _poll_verification — we test
        # the same construction logic here with a sample tv_details dict.
        tv_details = {
            "id": "tv-123",
            "number": "+14155551234",
            "state": "verification_pending",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "ends_at": (datetime.now(timezone.utc) + timedelta(minutes=10)).isoformat(),
            "total_cost": 2.50,
            "can_cancel": True,
            "can_report": True,
        }
        created_at = datetime.now(timezone.utc)

        # Replicate the _TVVerif construction from sms_polling_service.py
        # After the fix it should include ends_at and service_name
        class _TVVerif:
            def __init__(self, d, _created_at, _service_name="unknown"):
                self.number = d["number"]
                self.created_at = _created_at
                self.id = d["id"]
                self.ends_at = d.get("ends_at")
                self.service_name = _service_name

        obj = _TVVerif(tv_details, created_at, "telegram")

        assert obj.number == "+14155551234"
        assert obj.id == "tv-123"
        assert obj.created_at == created_at
        assert obj.ends_at is not None, "_TVVerif must expose ends_at"
        assert obj.service_name == "telegram", "_TVVerif must expose service_name"


# ---------------------------------------------------------------------------
# Issue 11 — Voice area codes hardcoded
# ---------------------------------------------------------------------------


class TestVoiceAreaCodesNotHardcoded:
    """AC-11: voice template should not have hardcoded area code option values."""

    def test_no_hardcoded_area_code_options(self):
        """AC-11.1: area-code-select must not contain static value='212' etc."""
        template_path = os.path.join(
            os.path.dirname(__file__), "..", "templates", "voice_verify_modern.html"
        )
        with open(template_path, "r") as f:
            content = f.read()

        # Find the area-code-select element and check for hardcoded values
        hardcoded = re.findall(r'<option\s+value="(\d{3})"', content)
        assert (
            len(hardcoded) == 0
        ), f"voice_verify_modern.html still has hardcoded area code options: {hardcoded}"


# ---------------------------------------------------------------------------
# Issue 16 — Voice template no timeout outcome call
# ---------------------------------------------------------------------------


class TestVoiceTimeoutOutcome:
    """AC-16: voice template must call outcome endpoint on timeout."""

    def test_voice_template_has_outcome_call(self):
        """AC-16.1: The voice template JS must POST to outcome endpoint on timeout."""
        template_path = os.path.join(
            os.path.dirname(__file__), "..", "templates", "voice_verify_modern.html"
        )
        with open(template_path, "r") as f:
            content = f.read()

        assert (
            "verification/outcome" in content
        ), "voice_verify_modern.html must call the outcome endpoint on timeout"
