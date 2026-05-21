"""Comprehensive tests for verification endpoints."""

from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.core.dependencies import get_current_user_id
from app.models.verification import Verification
from main import app


@pytest.fixture(autouse=True)
def mock_purchase_endpoints_tv_service(monkeypatch):
    """Mock TextVerified service in purchase_endpoints for all tests."""
    mock_service = MagicMock()
    mock_service.enabled = True
    mock_service.get_services_list = AsyncMock(
        return_value=[
            {"id": "telegram", "name": "Telegram", "price": 0.50},
            {"id": "whatsapp", "name": "WhatsApp", "price": 0.75},
            {"id": "instagram", "name": "Instagram", "price": 0.60},
        ]
    )
    mock_service.get_sms = AsyncMock(return_value=None)
    mock_service.cancel_number = AsyncMock()

    monkeypatch.setattr(
        "app.api.verification.purchase_endpoints._tv_service", mock_service
    )
    return mock_service


class TestVerificationEndpoints:
    """Test verification endpoints comprehensively."""

    def test_get_available_services_success(self, client, mock_textverified_service):
        """Test getting available services."""
        response = client.get("/api/countries/US/services")
        assert response.status_code == 200
        data = response.json()
        assert "services" in data
        assert data["total"] >= 3  # At least 3 services from mock
        assert data["source"] in ["api", "cache", "warming", "dev-fallback"]

    def test_get_available_services_unavailable(self, client):
        """Test getting services when TextVerified is unavailable."""
        with patch("app.services.textverified_service.TextVerifiedService") as mock_tv:
            mock_instance = MagicMock()
            mock_instance.enabled = False
            mock_instance.get_services_list = AsyncMock(
                side_effect=RuntimeError("TextVerified API is not configured")
            )
            mock_tv.return_value = mock_instance

            response = client.get("/api/countries/US/services")
            assert response.status_code == 200  # Returns 200 with error in body
            data = response.json()
            assert "error" in data or "dev_mode" in data  # Dev mode returns fallback

    def test_create_verification_success(
        self, authenticated_regular_client, regular_user, db
    ):
        """Test successful verification creation."""
        # Ensure user has sufficient credits
        regular_user.credits = 10.0
        db.commit()

        with patch(
            "app.services.providers.provider_router.ProviderRouter"
        ) as mock_router:
            mock_router_instance = MagicMock()
            mock_router_instance.get_enabled_providers = MagicMock(
                return_value=["textverified"]
            )

            from app.services.providers.base_provider import PurchaseResult

            mock_purchase_result = PurchaseResult(
                phone_number="+12025551234",
                order_id="tv-123",
                cost=0.50,
                expires_at="2026-05-21T12:00:00Z",
                provider="textverified",
                operator="T-Mobile",
                assigned_area_code="202",
                area_code_matched=True,
                fallback_applied=False,
                same_state_fallback=False,
                retry_attempts=0,
                voip_rejected=False,
                routing_reason="primary",
                city_honoured=False,
                city_note=None,
                requested_area_code=None,
            )
            mock_router_instance.purchase_with_failover = AsyncMock(
                return_value=mock_purchase_result
            )
            mock_router.return_value = mock_router_instance

            response = authenticated_regular_client.post(
                "/api/verification/request",
                json={"service": "telegram", "country": "US", "capability": "sms"},
            )

        assert response.status_code == 201
        data = response.json()
        assert data["success"] is True
        assert "verification_id" in data
        assert data["service"] == "telegram"
        assert data["phone_number"] == "+12025551234"
        assert data["status"] == "pending"

    def test_create_verification_insufficient_credits(
        self, authenticated_regular_client, regular_user, db
    ):
        """Test verification creation with insufficient credits."""
        regular_user.credits = 0.0
        regular_user.free_verifications = 0
        db.commit()

        with patch(
            "app.services.providers.provider_router.ProviderRouter"
        ) as mock_router:
            mock_router_instance = MagicMock()
            mock_router_instance.get_enabled_providers = MagicMock(
                return_value=["textverified"]
            )
            mock_router.return_value = mock_router_instance

            response = authenticated_regular_client.post(
                "/api/verification/request",
                json={"service": "telegram", "country": "US", "capability": "sms"},
            )

        assert response.status_code == 402
        data = response.json()
        error_msg = (data.get("detail") or data.get("message") or "").lower()
        assert "insufficient" in error_msg or "credit" in error_msg

    def test_create_verification_with_free_verifications(
        self, authenticated_regular_client, regular_user, db
    ):
        """Test verification creation using free verifications."""
        regular_user.free_verifications = 5
        regular_user.credits = 0.0
        db.commit()

        with patch(
            "app.services.providers.provider_router.ProviderRouter"
        ) as mock_router:
            mock_router_instance = MagicMock()
            mock_router_instance.get_enabled_providers = MagicMock(
                return_value=["textverified"]
            )

            from app.services.providers.base_provider import PurchaseResult

            mock_purchase_result = PurchaseResult(
                phone_number="+12025551234",
                order_id="tv-123",
                cost=0.50,
                expires_at="2026-05-21T12:00:00Z",
                provider="textverified",
                operator="T-Mobile",
                assigned_area_code="202",
                area_code_matched=True,
                fallback_applied=False,
                same_state_fallback=False,
                retry_attempts=0,
                voip_rejected=False,
                routing_reason="primary",
                city_honoured=False,
                city_note=None,
                requested_area_code=None,
            )
            mock_router_instance.purchase_with_failover = AsyncMock(
                return_value=mock_purchase_result
            )
            mock_router.return_value = mock_router_instance

            response = authenticated_regular_client.post(
                "/api/verification/request",
                json={"service": "telegram", "country": "US", "capability": "sms"},
            )

        assert response.status_code == 201
        db.refresh(regular_user)
        assert regular_user.free_verifications == 4

    def test_create_verification_missing_service(self, authenticated_regular_client):
        """Test verification creation without service name."""
        response = authenticated_regular_client.post(
            "/api/verification/request", json={"country": "US", "capability": "sms"}
        )

        assert response.status_code == 422  # Validation error

    def test_create_verification_idempotency(
        self, authenticated_regular_client, regular_user, db
    ):
        """Test idempotency key prevents duplicate verifications."""
        import uuid

        unique_key = str(uuid.uuid4())

        verification = Verification(
            user_id=regular_user.id,
            service_name="telegram",
            phone_number="+12025551234",
            status="pending",
            cost=0.50,
            capability="sms",
            country="US",
            idempotency_key=unique_key,
            created_at=datetime.now(timezone.utc),
        )
        db.add(verification)
        db.commit()

        response = authenticated_regular_client.post(
            "/api/verification/request",
            json={
                "service": "telegram",
                "country": "US",
                "capability": "sms",
                "idempotency_key": unique_key,
            },
        )

        assert response.status_code == 201
        data = response.json()
        assert data["verification_id"] == verification.id

    def test_create_verification_with_area_code(self, client, payg_user, db):
        """Test verification creation with area code selection."""

        def override_get_current_user_id():
            return str(payg_user.id)

        app.dependency_overrides[get_current_user_id] = override_get_current_user_id

        try:
            with patch(
                "app.services.providers.provider_router.ProviderRouter"
            ) as mock_router:
                mock_router_instance = MagicMock()
                mock_router_instance.get_enabled_providers = MagicMock(
                    return_value=["textverified"]
                )

                from app.services.providers.base_provider import PurchaseResult

                mock_purchase_result = PurchaseResult(
                    phone_number="+12025551234",
                    order_id="tv-123",
                    cost=0.50,
                    expires_at="2026-05-21T12:00:00Z",
                    provider="textverified",
                    operator="T-Mobile",
                    assigned_area_code="202",
                    area_code_matched=True,
                    fallback_applied=False,
                    same_state_fallback=False,
                    retry_attempts=0,
                    voip_rejected=False,
                    routing_reason="primary",
                    city_honoured=False,
                    city_note=None,
                    requested_area_code=None,
                )
                mock_router_instance.purchase_with_failover = AsyncMock(
                    return_value=mock_purchase_result
                )
                mock_router.return_value = mock_router_instance

                response = client.post(
                    "/api/verification/request",
                    json={
                        "service": "telegram",
                        "country": "US",
                        "capability": "sms",
                        "area_codes": ["202"],
                    },
                )

            assert response.status_code in [201, 402, 403]
        finally:
            app.dependency_overrides.clear()

    def test_create_verification_area_code_tier_restriction(
        self, authenticated_regular_client
    ):
        """Test area code selection requires PayG tier."""
        with patch(
            "app.services.providers.provider_router.ProviderRouter"
        ) as mock_router:
            mock_router_instance = MagicMock()
            mock_router_instance.get_enabled_providers = MagicMock(
                return_value=["textverified"]
            )
            mock_router.return_value = mock_router_instance

            response = authenticated_regular_client.post(
                "/api/verification/request",
                json={
                    "service": "telegram",
                    "country": "US",
                    "capability": "sms",
                    "area_codes": ["202"],
                },
            )

        assert response.status_code in [402, 403]

    def test_create_verification_with_carrier(self, authenticated_pro_client, db):
        """Test verification creation with carrier filtering."""
        with patch(
            "app.services.providers.provider_router.ProviderRouter"
        ) as mock_router:
            mock_router_instance = MagicMock()
            mock_router_instance.get_enabled_providers = MagicMock(
                return_value=["textverified"]
            )

            from app.services.providers.base_provider import PurchaseResult

            mock_purchase_result = PurchaseResult(
                phone_number="+12025551234",
                order_id="tv-123",
                cost=0.50,
                expires_at="2026-05-21T12:00:00Z",
                provider="textverified",
                operator="T-Mobile",
                assigned_area_code="202",
                area_code_matched=True,
                fallback_applied=False,
                same_state_fallback=False,
                retry_attempts=0,
                voip_rejected=False,
                routing_reason="primary",
                city_honoured=False,
                city_note=None,
                requested_area_code=None,
            )
            mock_router_instance.purchase_with_failover = AsyncMock(
                return_value=mock_purchase_result
            )
            mock_router.return_value = mock_router_instance

            response = authenticated_pro_client.post(
                "/api/verification/request",
                json={
                    "service": "telegram",
                    "country": "US",
                    "capability": "sms",
                    "carrier": "verizon",
                },
            )

        assert response.status_code == 201

    def test_create_verification_carrier_tier_restriction(self, client, payg_user):
        """Test carrier filtering (ignored now, returns 201)."""

        def override_get_current_user_id():
            return str(payg_user.id)

        app.dependency_overrides[get_current_user_id] = override_get_current_user_id

        try:
            with patch(
                "app.services.providers.provider_router.ProviderRouter"
            ) as mock_router:
                mock_router_instance = MagicMock()
                mock_router_instance.get_enabled_providers = MagicMock(
                    return_value=["textverified"]
                )

                from app.services.providers.base_provider import PurchaseResult

                mock_purchase_result = PurchaseResult(
                    phone_number="+12025551234",
                    order_id="tv-123",
                    cost=0.50,
                    expires_at="2026-05-21T12:00:00Z",
                    provider="textverified",
                    operator="T-Mobile",
                    assigned_area_code="202",
                    area_code_matched=True,
                    fallback_applied=False,
                    same_state_fallback=False,
                    retry_attempts=0,
                    voip_rejected=False,
                    routing_reason="primary",
                    city_honoured=False,
                    city_note=None,
                    requested_area_code=None,
                )
                mock_router_instance.purchase_with_failover = AsyncMock(
                    return_value=mock_purchase_result
                )
                mock_router.return_value = mock_router_instance

                response = client.post(
                    "/api/verification/request",
                    json={
                        "service": "telegram",
                        "country": "US",
                        "capability": "sms",
                        "carrier": "verizon",
                    },
                )

            assert response.status_code == 201
        finally:
            app.dependency_overrides.clear()

    def test_get_verification_status_success(
        self, authenticated_regular_client, regular_user, db
    ):
        """Test getting verification status."""
        verification = Verification(
            user_id=regular_user.id,
            service_name="telegram",
            phone_number="+12025551234",
            status="pending",
            cost=0.50,
            capability="sms",
            country="US",
        )
        db.add(verification)
        db.commit()

        response = authenticated_regular_client.get(
            f"/api/verification/status/{verification.id}"
        )
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == verification.id
        assert data["status"] == "pending"
        assert data["phone_number"] == "+12025551234"

    def test_get_verification_status_not_found(self, authenticated_regular_client):
        """Test getting status for non-existent verification."""
        response = authenticated_regular_client.get(
            "/api/verification/status/nonexistent-id"
        )
        assert response.status_code == 404

    def test_get_verification_history_success(
        self, authenticated_regular_client, regular_user, db
    ):
        """Test getting verification history."""
        for i in range(3):
            verification = Verification(
                user_id=regular_user.id,
                service_name=f"service{i}",
                phone_number=f"+1202555{i:04d}",
                status="completed",
                cost=0.50,
                capability="sms",
                country="US",
            )
            db.add(verification)
        db.commit()

        response = authenticated_regular_client.get("/api/verify/history")

        assert response.status_code == 200
        data = response.json()
        assert "verifications" in data
        assert data["total"] >= 3
        assert len(data["verifications"]) >= 3

    def test_get_verification_history_pagination(
        self, authenticated_regular_client, regular_user, db
    ):
        """Test verification history pagination."""
        for i in range(10):
            verification = Verification(
                user_id=regular_user.id,
                service_name=f"service{i}",
                phone_number=f"+1202555{i:04d}",
                status="completed",
                cost=0.50,
                capability="sms",
                country="US",
            )
            db.add(verification)
        db.commit()

        response = authenticated_regular_client.get(
            "/api/verify/history?limit=5&offset=0"
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data["verifications"]) == 5
        assert data["total"] >= 10

    def test_get_verification_history_empty(self, authenticated_regular_client):
        """Test getting history when no verifications exist."""
        response = authenticated_regular_client.get("/api/verify/history")

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 0
        assert len(data["verifications"]) == 0

    def test_get_verification_status_polling_pending(
        self, authenticated_regular_client, regular_user, db
    ):
        """Test polling for pending verification."""
        verification = Verification(
            user_id=regular_user.id,
            service_name="telegram",
            phone_number="+12025551234",
            status="pending",
            cost=0.50,
            capability="sms",
            country="US",
            activation_id="tv-123",
        )
        db.add(verification)
        db.commit()

        with patch(
            "app.api.verification.status_polling.TextVerifiedService"
        ) as mock_tv:
            mock_instance = MagicMock()
            mock_instance.get_verification_status = AsyncMock(
                return_value={"status": "pending"}
            )
            mock_tv.return_value = mock_instance

            response = authenticated_regular_client.get(
                f"/api/verification/status/{verification.id}"
            )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "pending"
        assert data["sms_code"] is None

    def test_get_verification_status_polling_completed(
        self, authenticated_regular_client, regular_user, db
    ):
        """Test polling when SMS is received."""
        verification = Verification(
            user_id=regular_user.id,
            service_name="telegram",
            phone_number="+12025551234",
            status="pending",
            cost=0.50,
            capability="sms",
            country="US",
            activation_id="tv-123",
        )
        db.add(verification)
        db.commit()

        with patch(
            "app.api.verification.status_polling.TextVerifiedService"
        ) as mock_tv:
            mock_instance = MagicMock()
            mock_instance.get_verification_status = AsyncMock(
                return_value={
                    "status": "completed",
                    "sms_code": "123456",
                    "sms_text": "Your code is 123456",
                }
            )
            mock_tv.return_value = mock_instance

            response = authenticated_regular_client.get(
                f"/api/verification/status/{verification.id}"
            )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "completed"
        assert data["sms_code"] == "123456"

    def test_get_verification_status_polling_not_found(
        self, authenticated_regular_client
    ):
        """Test polling for non-existent verification."""
        response = authenticated_regular_client.get(
            "/api/verification/status/nonexistent-id"
        )

        assert response.status_code == 404

    def test_cancel_verification_success(
        self, authenticated_regular_client, regular_user, db
    ):
        """Test canceling verification."""
        verification = Verification(
            user_id=regular_user.id,
            service_name="telegram",
            phone_number="+12025551234",
            status="pending",
            cost=0.50,
            capability="sms",
            country="US",
            activation_id="tv-123",
            provider="textverified",
        )
        db.add(verification)
        db.commit()

        with patch(
            "app.services.providers.provider_router.ProviderRouter"
        ) as mock_router:
            mock_router_instance = MagicMock()
            mock_router_instance.get_enabled_providers = MagicMock(
                return_value=["textverified"]
            )

            # Mock the adapter cancel method
            with patch(
                "app.services.providers.textverified_adapter.TextVerifiedAdapter"
            ) as mock_adapter:
                mock_adapter_instance = MagicMock()
                mock_adapter_instance.cancel = AsyncMock(return_value=True)
                mock_adapter.return_value = mock_adapter_instance

                response = authenticated_regular_client.post(
                    f"/api/verification/cancel/{verification.id}"
                )

        assert response.status_code == 200
        db.refresh(verification)
        assert verification.status == "cancelled"

    def test_cancel_verification_not_found(self, authenticated_regular_client):
        """Test canceling non-existent verification."""
        response = authenticated_regular_client.post(
            "/api/verification/cancel/nonexistent-id"
        )

        assert response.status_code == 404

    def test_cancel_verification_already_completed(
        self, authenticated_regular_client, regular_user, db
    ):
        """Test canceling already completed verification."""
        verification = Verification(
            user_id=regular_user.id,
            service_name="telegram",
            phone_number="+12025551234",
            status="completed",
            cost=0.50,
            capability="sms",
            country="US",
            sms_code="123456",
        )
        db.add(verification)
        db.commit()

        response = authenticated_regular_client.post(
            f"/api/verification/cancel/{verification.id}"
        )

        assert response.status_code == 400
        db.refresh(verification)
        assert verification.status == "completed"

    def test_create_verification_service_unavailable(
        self, authenticated_regular_client
    ):
        """Test verification creation when service is unavailable."""
        with patch(
            "app.services.providers.provider_router.ProviderRouter"
        ) as mock_router:
            mock_router_instance = MagicMock()
            mock_router_instance.get_enabled_providers = MagicMock(return_value=[])
            mock_router.return_value = mock_router_instance

            response = authenticated_regular_client.post(
                "/api/verification/request",
                json={"service": "telegram", "country": "US", "capability": "sms"},
            )

        assert response.status_code == 503

    def test_create_verification_user_not_found(self, client, db):
        """Test verification creation with non-existent user."""

        def override_get_current_user_id():
            return "nonexistent-user"

        app.dependency_overrides[get_current_user_id] = override_get_current_user_id

        try:
            response = client.post(
                "/api/verification/request",
                json={"service": "telegram", "country": "US", "capability": "sms"},
            )

            assert response.status_code == 404
        finally:
            app.dependency_overrides.clear()
