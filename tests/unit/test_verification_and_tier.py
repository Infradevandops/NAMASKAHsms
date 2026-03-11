"""Unit tests for verification routes and tier upgrade."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime


# ── Helpers ──────────────────────────────────────────────────────────────────


def _make_user(credits=10.0, tier="freemium"):
    u = MagicMock()
    u.id = "user-1"
    u.email = "test@example.com"
    u.credits = credits
    u.subscription_tier = tier
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


# ── POST /verify/create ───────────────────────────────────────────────────────


class TestCreateVerification:

    @pytest.mark.asyncio
    async def test_insufficient_credits_returns_402(self):
        from app.api.verification.verification_routes import create_verification
        from app.schemas.verification import VerificationCreate
        from fastapi import HTTPException

        db = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = _make_user(
            credits=1.0
        )

        with pytest.raises(HTTPException) as exc:
            await create_verification(
                verification_data=VerificationCreate(
                    service="whatsapp", country="US", capability="sms"
                ),
                user_id="user-1",
                db=db,
            )
        assert exc.value.status_code == 402

    @pytest.mark.asyncio
    async def test_capability_stored_on_record(self):
        from app.api.verification.verification_routes import create_verification
        from app.schemas.verification import VerificationCreate

        user = _make_user(credits=10.0)
        db = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = user

        purchase_result = {
            "success": True,
            "phone_number": "+12025551234",
            "cost": 2.50,
            "verification_id": "act-123",
        }

        with patch(
            "app.api.verification.verification_routes.TextVerifiedService"
        ) as MockTV, patch(
            "app.api.verification.verification_routes.NotificationDispatcher"
        ):
            tv = MockTV.return_value
            tv.enabled = True
            tv.purchase_number = AsyncMock(return_value=purchase_result)

            result = await create_verification(
                verification_data=VerificationCreate(
                    service="whatsapp", country="US", capability="voice"
                ),
                user_id="user-1",
                db=db,
            )

        assert result["id"] is not None
        assert db.add.called
        added = db.add.call_args[0][0]
        assert added.capability == "voice"
        assert added.activation_id == "act-123"

    @pytest.mark.asyncio
    async def test_balance_deducted_on_success(self):
        from app.api.verification.verification_routes import create_verification
        from app.schemas.verification import VerificationCreate

        user = _make_user(credits=10.0)
        db = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = user

        with patch(
            "app.api.verification.verification_routes.TextVerifiedService"
        ) as MockTV, patch(
            "app.api.verification.verification_routes.NotificationDispatcher"
        ):
            tv = MockTV.return_value
            tv.enabled = True
            tv.purchase_number = AsyncMock(
                return_value={
                    "success": True,
                    "phone_number": "+1234",
                    "cost": 2.50,
                    "verification_id": "act-1",
                }
            )

            await create_verification(
                verification_data=VerificationCreate(service="whatsapp"),
                user_id="user-1",
                db=db,
            )

        assert user.credits == pytest.approx(7.50)


# ── GET /verify/{id}/status ───────────────────────────────────────────────────


class TestVerificationStatus:

    @pytest.mark.asyncio
    async def test_returns_sms_code_when_completed(self):
        from app.api.verification.verification_routes import get_verification_status

        v = _make_verification(status="completed", sms_code="123456")
        db = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = v

        result = await get_verification_status("verif-1", user_id="user-1", db=db)

        assert result["status"] == "completed"
        assert result["sms_code"] == "123456"

    @pytest.mark.asyncio
    async def test_returns_404_for_wrong_user(self):
        from app.api.verification.verification_routes import get_verification_status
        from fastapi import HTTPException

        db = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = None

        with pytest.raises(HTTPException) as exc:
            await get_verification_status("verif-1", user_id="other-user", db=db)
        assert exc.value.status_code == 404


# ── GET /verify/{id}/sms ──────────────────────────────────────────────────────


class TestVerificationSms:

    @pytest.mark.asyncio
    async def test_uses_activation_id_not_db_uuid(self):
        from app.api.verification.verification_routes import get_verification_sms

        v = _make_verification(activation_id="act-xyz")
        db = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = v

        with patch(
            "app.api.verification.verification_routes.TextVerifiedService"
        ) as MockTV, patch(
            "app.api.verification.verification_routes.NotificationDispatcher"
        ):
            tv = MockTV.return_value
            tv.enabled = True
            tv.get_sms = AsyncMock(
                return_value={"success": False, "sms": None, "code": None}
            )

            await get_verification_sms("verif-1", user_id="user-1", db=db)

            tv.get_sms.assert_called_once_with("act-xyz")

    @pytest.mark.asyncio
    async def test_stores_sms_text_and_code_on_completion(self):
        from app.api.verification.verification_routes import get_verification_sms

        v = _make_verification(activation_id="act-xyz")
        db = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = v

        with patch(
            "app.api.verification.verification_routes.TextVerifiedService"
        ) as MockTV, patch(
            "app.api.verification.verification_routes.NotificationDispatcher"
        ):
            tv = MockTV.return_value
            tv.enabled = True
            tv.get_sms = AsyncMock(
                return_value={
                    "success": True,
                    "sms": "Your code is 9876",
                    "code": "9876",
                }
            )

            await get_verification_sms("verif-1", user_id="user-1", db=db)

        assert v.sms_text == "Your code is 9876"
        assert v.sms_code == "9876"
        assert v.status == "completed"


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
        db = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = user

        result = await upgrade_tier(target_tier="pro", user_id="user-1", db=db)

        assert result["status"] == "pending_payment"
        assert user.subscription_tier == "freemium"  # unchanged

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
