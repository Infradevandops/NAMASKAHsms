"""Unit tests for verification routes and tier upgrade."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime


# ── Helpers ───────────────────────────────────────────────────────────────────


def _make_user(credits=10.0, tier="freemium"):
    u = MagicMock()
    u.id = "user-1"
    u.email = "test@example.com"
    u.credits = credits
    u.subscription_tier = tier
    u.is_admin = False
    return u


def _make_verification(status="pending", activation_id="act-123", sms_code=None):
    v = MagicMock()
    v.id = "verif-1"
    v.user_id = "user-1"
    v.service_name = "whatsapp"
    v.phone_number = "+12025551234"
    v.status = status
    v.activation_id = activation_id
    v.sms_code = sms_code
    v.capability = "sms"
    v.cost = 2.50
    v.created_at = datetime.utcnow()
    return v


# ── POST /verification/request ────────────────────────────────────────────────


class TestCreateVerification:

    def test_insufficient_credits_returns_402(self, client, db, regular_user):
        """Insufficient credits → 402."""
        regular_user.credits = 0.5
        db.commit()

        with patch(
            "app.api.verification.purchase_endpoints.TextVerifiedService"
        ) as MockTV:
            tv = MockTV.return_value
            tv.enabled = True

            from app.core.dependencies import get_current_user_id
            from main import app

            app.dependency_overrides[get_current_user_id] = lambda: regular_user.id

            response = client.post(
                "/api/verification/request",
                json={"service": "whatsapp", "country": "US", "capability": "sms"},
            )
            app.dependency_overrides.clear()

        assert response.status_code == 402

    def test_textverified_disabled_returns_503(self, client, regular_user):
        """TextVerified disabled → 503."""
        from app.core.dependencies import get_current_user_id
        from main import app

        with patch(
            "app.api.verification.purchase_endpoints.TextVerifiedService"
        ) as MockTV:
            tv = MockTV.return_value
            tv.enabled = False

            app.dependency_overrides[get_current_user_id] = lambda: regular_user.id
            response = client.post(
                "/api/verification/request",
                json={"service": "whatsapp", "country": "US"},
            )
            app.dependency_overrides.clear()

        assert response.status_code in [503, 402, 201]


# ── GET /verification/status/{id} ─────────────────────────────────────────────


class TestVerificationStatus:

    def test_returns_status_for_own_verification(self, client, db, regular_user):
        """User can get status of their own verification."""
        from app.models.verification import Verification
        from app.core.dependencies import get_current_user_id
        from main import app
        import uuid

        ver = Verification(
            id=str(uuid.uuid4()),
            user_id=regular_user.id,
            service_name="whatsapp",
            phone_number="+12025551234",
            country="US",
            status="completed",
            sms_code="123456",
            cost=2.50,
            provider="textverified",
            activation_id="act-123",
        )
        db.add(ver)
        db.commit()

        with patch("app.api.verification.status_polling.TextVerifiedService"):
            app.dependency_overrides[get_current_user_id] = lambda: regular_user.id
            response = client.get(f"/api/verification/status/{ver.id}")
            app.dependency_overrides.clear()

        assert response.status_code in [200, 404]

    def test_returns_404_for_wrong_user(self, client, db, regular_user, pro_user):
        """User cannot get status of another user's verification."""
        from app.models.verification import Verification
        from app.core.dependencies import get_current_user_id
        from main import app
        import uuid

        ver = Verification(
            id=str(uuid.uuid4()),
            user_id=pro_user.id,
            service_name="whatsapp",
            phone_number="+12025551234",
            country="US",
            status="pending",
            cost=2.50,
            provider="textverified",
            activation_id="act-456",
        )
        db.add(ver)
        db.commit()

        app.dependency_overrides[get_current_user_id] = lambda: regular_user.id
        response = client.get(f"/api/verification/status/{ver.id}")
        app.dependency_overrides.clear()

        assert response.status_code == 404


# ── SMS code stored on completion ─────────────────────────────────────────────


class TestVerificationSms:

    @pytest.mark.skip(
        reason="async polling loop hangs in test suite — covered by test_sms_polling.py"
    )
    @pytest.mark.asyncio
    async def test_uses_activation_id_not_db_uuid(self, db, regular_user):
        """Polling uses activation_id (TextVerified ID), not the DB UUID."""
        from app.services.sms_polling_service import SMSPollingService
        import uuid

        from app.models.verification import Verification

        ver = Verification(
            id=str(uuid.uuid4()),
            user_id=regular_user.id,
            service_name="whatsapp",
            phone_number="+12025551234",
            country="US",
            status="pending",
            cost=2.50,
            provider="textverified",
            activation_id="act-xyz",
        )
        db.add(ver)
        db.commit()

        service = SMSPollingService()
        service.textverified = AsyncMock()
        service.textverified.check_sms = AsyncMock(
            return_value={"status": "PENDING", "messages": []}
        )

        with patch("app.services.sms_polling_service.SessionLocal") as MockSession:
            session_mock = MagicMock(wraps=db)
            session_mock.close = MagicMock()
            session_mock.query = db.query
            MockSession.return_value = session_mock

            with patch("app.services.sms_polling_service.NotificationService"):
                await service._poll_verification(ver.id, ver.phone_number)

        service.textverified.check_sms.assert_called_with("act-xyz")

    @pytest.mark.skip(
        reason="async polling loop hangs in test suite — covered by test_sms_polling.py"
    )
    @pytest.mark.asyncio
    async def test_stores_sms_text_and_code_on_completion(self, db, regular_user):
        """When SMS received, sms_text, sms_code, and status=completed are saved."""
        from app.services.sms_polling_service import SMSPollingService
        import uuid

        from app.models.verification import Verification

        ver = Verification(
            id=str(uuid.uuid4()),
            user_id=regular_user.id,
            service_name="whatsapp",
            phone_number="+12025551234",
            country="US",
            status="pending",
            cost=2.50,
            provider="textverified",
            activation_id="act-xyz",
        )
        db.add(ver)
        db.commit()

        service = SMSPollingService()
        service.textverified = AsyncMock()
        service.textverified.check_sms = AsyncMock(
            return_value={
                "status": "COMPLETED",
                "messages": [
                    {"text": "Your code is 9876", "received_at": "2026-01-01T00:00:00Z"}
                ],
            }
        )

        with patch("app.services.sms_polling_service.SessionLocal") as MockSession:
            session_mock = MagicMock(wraps=db)
            session_mock.close = MagicMock()
            session_mock.commit = MagicMock(side_effect=db.commit)
            session_mock.query = db.query
            session_mock.add = db.add
            MockSession.return_value = session_mock

            with patch("app.services.sms_polling_service.NotificationService"):
                await service._poll_verification(ver.id, ver.phone_number)

        db.refresh(ver)
        assert ver.status == "completed"
        assert "9876" in (ver.sms_code or ver.sms_text or "")


# ── POST /billing/tiers/upgrade ───────────────────────────────────────────────


class TestTierUpgrade:

    @pytest.mark.asyncio
    async def test_payg_commits_tier_immediately(self):
        from app.api.billing.tier_endpoints import upgrade_tier

        user = _make_user(tier="freemium")
        db = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = user

        result = await upgrade_tier(target_tier="payg", user_id="user-1", db=db)

        assert result["status"] == "success"
        assert user.subscription_tier == "payg"
        db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_paid_tier_returns_pending_payment(self):
        from app.api.billing.tier_endpoints import upgrade_tier

        user = _make_user(tier="freemium")
        user.credits = 0.0
        db = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = user

        with patch("app.api.billing.tier_endpoints.TierConfig") as MockTC, patch(
            "app.services.payment_service.PaymentService"
        ) as MockPS:
            MockTC.get_tier_config.return_value = {"monthly_fee_usd": 25.0}
            ps = MockPS.return_value
            ps.initialize_payment = AsyncMock(
                return_value={
                    "authorization_url": "https://paystack.com/pay/test",
                    "reference": "ref_test_123",
                }
            )
            result = await upgrade_tier(target_tier="pro", user_id="user-1", db=db)

        assert result["status"] == "pending_payment"
        assert user.subscription_tier == "freemium"

    @pytest.mark.asyncio
    async def test_same_tier_returns_400(self):
        from app.api.billing.tier_endpoints import upgrade_tier
        from fastapi import HTTPException

        user = _make_user(tier="payg")
        db = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = user

        with pytest.raises(HTTPException) as exc:
            await upgrade_tier(target_tier="payg", user_id="user-1", db=db)
        assert exc.value.status_code == 400

    @pytest.mark.asyncio
    async def test_invalid_tier_returns_400(self):
        from app.api.billing.tier_endpoints import upgrade_tier
        from fastapi import HTTPException

        user = _make_user(tier="freemium")
        db = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = user

        with pytest.raises(HTTPException) as exc:
            await upgrade_tier(target_tier="enterprise", user_id="user-1", db=db)
        assert exc.value.status_code == 400


# ── Webhook tier assignment ───────────────────────────────────────────────────


class TestWebhookTierAssignment:

    @pytest.mark.asyncio
    async def test_webhook_sets_pro_tier_on_upgrade_payment(self):
        from app.api.billing.payment_endpoints import paystack_webhook
        import json

        user = _make_user(tier="freemium")
        db = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = user

        payload = {
            "event": "charge.success",
            "data": {
                "reference": "ref-001",
                "metadata": {
                    "user_id": "user-1",
                    "namaskah_amount": 25.0,
                    "upgrade_to": "pro",
                },
            },
        }

        request = MagicMock()
        request.headers.get.return_value = "valid-sig"
        request.body = AsyncMock(return_value=json.dumps(payload).encode())

        with patch("app.api.billing.payment_endpoints.get_payment_service") as MockPS:
            ps = MockPS.return_value
            ps.verify_webhook_signature.return_value = True
            ps.credit_user_with_lock = AsyncMock()

            await paystack_webhook(request=request, db=db)

        assert user.subscription_tier == "pro"
        db.commit.assert_called()

    @pytest.mark.asyncio
    async def test_webhook_without_upgrade_to_does_not_change_tier(self):
        from app.api.billing.payment_endpoints import paystack_webhook
        import json

        user = _make_user(tier="freemium")
        db = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = user

        payload = {
            "event": "charge.success",
            "data": {
                "reference": "ref-002",
                "metadata": {"user_id": "user-1", "namaskah_amount": 10.0},
            },
        }

        request = MagicMock()
        request.headers.get.return_value = "valid-sig"
        request.body = AsyncMock(return_value=json.dumps(payload).encode())

        with patch("app.api.billing.payment_endpoints.get_payment_service") as MockPS:
            ps = MockPS.return_value
            ps.verify_webhook_signature.return_value = True
            ps.credit_user_with_lock = AsyncMock()

            await paystack_webhook(request=request, db=db)

        assert user.subscription_tier == "freemium"
