"""Purchase endpoint integration tests — Phase 4, BROKEN_ITEMS.md.

Tests the full purchase flow with the provider router wired in,
verifying correct provider saved to DB and failover behaviour.
"""

from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from app.models.user import User
from app.models.verification import Verification
from app.services.providers.base_provider import PurchaseResult


def _make_purchase_result(provider="textverified", phone="+12025551234"):
    return PurchaseResult(
        phone_number=phone,
        order_id="order-test-123",
        cost=2.22,
        expires_at="2026-04-13T12:00:00Z",
        provider=provider,
        area_code_matched=True,
        carrier_matched=True,
        real_carrier=None,
        voip_rejected=False,
        fallback_applied=False,
        requested_area_code=None,
        assigned_area_code=None,
        same_state_fallback=True,
        retry_attempts=0,
        routing_reason=f"country=US",
        tv_object=None,
    )


@pytest.fixture
def auth_client(client, test_user_id):
    """Client with auth header injected."""
    from app.core.dependencies import get_current_user_id
    from main import app

    app.dependency_overrides[get_current_user_id] = lambda: test_user_id
    yield client
    app.dependency_overrides.clear()


@pytest.fixture
def funded_user(db, test_user_id):
    """User with enough credits to purchase."""
    user = db.query(User).filter(User.id == test_user_id).first()
    if not user:
        user = User(
            id=test_user_id,
            email="test@example.com",
            password_hash="$2b$12$testhash",
            credits=50.0,
            subscription_tier="pro",
            is_admin=False,
            created_at=datetime.now(timezone.utc),
        )
        db.add(user)
    else:
        user.credits = 50.0
    db.commit()
    return user


# ── Test 1: US routes to TextVerified ────────────────────────────────────────


def test_purchase_us_routes_textverified(auth_client, db, funded_user, test_user_id):
    """US request must use TextVerified and save provider='textverified' to DB."""
    result = _make_purchase_result(provider="textverified")

    with patch(
        "app.services.providers.provider_router.ProviderRouter"
    ) as MockRouter, patch(
        "app.api.verification.purchase_endpoints.PricingCalculator"
    ) as MockPricing, patch(
        "app.api.verification.purchase_endpoints.BalanceService"
    ) as MockBalance, patch(
        "app.api.verification.purchase_endpoints.TransactionService"
    ), patch(
        "app.api.verification.purchase_endpoints.NotificationDispatcher"
    ), patch(
        "app.api.verification.purchase_endpoints.RefundService"
    ) as MockRefund, patch(
        "app.api.verification.purchase_endpoints.QuotaService"
    ), patch(
        "app.api.verification.purchase_endpoints.sms_polling_service"
    ):

        MockRouter.return_value.purchase_with_failover = AsyncMock(return_value=result)
        MockRouter.return_value.get_enabled_providers.return_value = ["textverified"]
        MockPricing.calculate_sms_cost.return_value = {
            "total_cost": 2.22,
            "carrier_surcharge": 0.0,
            "area_code_surcharge": 0.0,
        }
        MockBalance.check_sufficient_balance = AsyncMock(
            return_value={
                "sufficient": True,
                "current_balance": 50.0,
                "source": "local",
            }
        )
        MockRefund.return_value.process_refund = AsyncMock(
            return_value={"refund_issued": False}
        )

        response = auth_client.post(
            "/api/verification/request",
            json={
                "service": "whatsapp",
                "country": "US",
                "capability": "sms",
            },
        )

    assert response.status_code == 201
    data = response.json()
    assert data["success"] is True

    # Verify DB record has correct provider
    verification = (
        db.query(Verification)
        .filter(Verification.activation_id == "order-test-123")
        .first()
    )
    assert verification is not None
    assert verification.provider == "textverified"
    assert verification.phone_number == "+12025551234"


# ── Test 2: International routes to 5sim ─────────────────────────────────────


def test_purchase_gb_routes_fivesim(auth_client, db, funded_user, test_user_id):
    """GB request must use 5sim and save provider='5sim' to DB."""
    result = _make_purchase_result(provider="5sim", phone="+447911123456")
    result.routing_reason = "country=GB"

    with patch(
        "app.services.providers.provider_router.ProviderRouter"
    ) as MockRouter, patch(
        "app.api.verification.purchase_endpoints.PricingCalculator"
    ) as MockPricing, patch(
        "app.api.verification.purchase_endpoints.BalanceService"
    ) as MockBalance, patch(
        "app.api.verification.purchase_endpoints.TransactionService"
    ), patch(
        "app.api.verification.purchase_endpoints.NotificationDispatcher"
    ), patch(
        "app.api.verification.purchase_endpoints.RefundService"
    ) as MockRefund, patch(
        "app.api.verification.purchase_endpoints.QuotaService"
    ), patch(
        "app.api.verification.purchase_endpoints.sms_polling_service"
    ):

        MockRouter.return_value.purchase_with_failover = AsyncMock(return_value=result)
        MockRouter.return_value.get_enabled_providers.return_value = ["fivesim"]
        MockPricing.calculate_sms_cost.return_value = {
            "total_cost": 2.50,
            "carrier_surcharge": 0.0,
            "area_code_surcharge": 0.0,
        }
        MockBalance.check_sufficient_balance = AsyncMock(
            return_value={
                "sufficient": True,
                "current_balance": 50.0,
                "source": "local",
            }
        )
        MockRefund.return_value.process_refund = AsyncMock(
            return_value={"refund_issued": False}
        )

        response = auth_client.post(
            "/api/verification/request",
            json={
                "service": "whatsapp",
                "country": "GB",
                "capability": "sms",
            },
        )

    assert response.status_code == 201

    verification = (
        db.query(Verification)
        .filter(Verification.phone_number == "+447911123456")
        .first()
    )
    assert verification is not None
    assert verification.provider == "5sim"
    assert verification.country == "GB"


# ── Test 3: provider field saved correctly ────────────────────────────────────


def test_verification_record_provider_field(auth_client, db, funded_user, test_user_id):
    """Verification record must store the exact provider name from PurchaseResult."""
    result = _make_purchase_result(provider="telnyx", phone="+4915123456789")
    result.routing_reason = "country=DE"

    with patch(
        "app.services.providers.provider_router.ProviderRouter"
    ) as MockRouter, patch(
        "app.api.verification.purchase_endpoints.PricingCalculator"
    ) as MockPricing, patch(
        "app.api.verification.purchase_endpoints.BalanceService"
    ) as MockBalance, patch(
        "app.api.verification.purchase_endpoints.TransactionService"
    ), patch(
        "app.api.verification.purchase_endpoints.NotificationDispatcher"
    ), patch(
        "app.api.verification.purchase_endpoints.RefundService"
    ) as MockRefund, patch(
        "app.api.verification.purchase_endpoints.QuotaService"
    ), patch(
        "app.api.verification.purchase_endpoints.sms_polling_service"
    ):

        MockRouter.return_value.purchase_with_failover = AsyncMock(return_value=result)
        MockRouter.return_value.get_enabled_providers.return_value = ["telnyx"]
        MockPricing.calculate_sms_cost.return_value = {
            "total_cost": 2.50,
            "carrier_surcharge": 0.0,
            "area_code_surcharge": 0.0,
        }
        MockBalance.check_sufficient_balance = AsyncMock(
            return_value={
                "sufficient": True,
                "current_balance": 50.0,
                "source": "local",
            }
        )
        MockRefund.return_value.process_refund = AsyncMock(
            return_value={"refund_issued": False}
        )

        response = auth_client.post(
            "/api/verification/request",
            json={
                "service": "telegram",
                "country": "DE",
                "capability": "sms",
            },
        )

    assert response.status_code == 201

    verification = (
        db.query(Verification)
        .filter(Verification.phone_number == "+4915123456789")
        .first()
    )
    assert verification is not None
    assert verification.provider == "telnyx"


# ── Test 4: failover success recorded correctly ───────────────────────────────


def test_purchase_failover_success(auth_client, db, funded_user, test_user_id):
    """When failover occurs, routing_reason reflects it and purchase still succeeds."""
    result = _make_purchase_result(provider="telnyx", phone="+447700900999")
    result.routing_reason = "failover from 5sim to telnyx"
    result.fallback_applied = True

    with patch(
        "app.services.providers.provider_router.ProviderRouter"
    ) as MockRouter, patch(
        "app.api.verification.purchase_endpoints.PricingCalculator"
    ) as MockPricing, patch(
        "app.api.verification.purchase_endpoints.BalanceService"
    ) as MockBalance, patch(
        "app.api.verification.purchase_endpoints.TransactionService"
    ), patch(
        "app.api.verification.purchase_endpoints.NotificationDispatcher"
    ), patch(
        "app.api.verification.purchase_endpoints.RefundService"
    ) as MockRefund, patch(
        "app.api.verification.purchase_endpoints.QuotaService"
    ), patch(
        "app.api.verification.purchase_endpoints.sms_polling_service"
    ):

        MockRouter.return_value.purchase_with_failover = AsyncMock(return_value=result)
        MockRouter.return_value.get_enabled_providers.return_value = ["telnyx"]
        MockPricing.calculate_sms_cost.return_value = {
            "total_cost": 2.50,
            "carrier_surcharge": 0.0,
            "area_code_surcharge": 0.0,
        }
        MockBalance.check_sufficient_balance = AsyncMock(
            return_value={
                "sufficient": True,
                "current_balance": 50.0,
                "source": "local",
            }
        )
        MockRefund.return_value.process_refund = AsyncMock(
            return_value={"refund_issued": False}
        )

        response = auth_client.post(
            "/api/verification/request",
            json={
                "service": "whatsapp",
                "country": "GB",
                "capability": "sms",
            },
        )

    assert response.status_code == 201
    data = response.json()
    assert data["success"] is True
    assert data["fallback_applied"] is True


# ── Test 5: business error does not failover ──────────────────────────────────


def test_purchase_business_error_no_failover(auth_client, funded_user, test_user_id):
    """RuntimeError with 'no inventory' must surface as 503, not silently failover."""
    with patch(
        "app.services.providers.provider_router.ProviderRouter"
    ) as MockRouter, patch(
        "app.api.verification.purchase_endpoints.PricingCalculator"
    ) as MockPricing, patch(
        "app.api.verification.purchase_endpoints.BalanceService"
    ) as MockBalance:

        MockRouter.return_value.purchase_with_failover = AsyncMock(
            side_effect=RuntimeError("No inventory available for GB")
        )
        MockRouter.return_value.get_enabled_providers.return_value = ["fivesim"]
        MockPricing.calculate_sms_cost.return_value = {
            "total_cost": 2.50,
            "carrier_surcharge": 0.0,
            "area_code_surcharge": 0.0,
        }
        MockBalance.check_sufficient_balance = AsyncMock(
            return_value={
                "sufficient": True,
                "current_balance": 50.0,
                "source": "local",
            }
        )

        response = auth_client.post(
            "/api/verification/request",
            json={
                "service": "whatsapp",
                "country": "GB",
                "capability": "sms",
            },
        )

    assert response.status_code == 503
