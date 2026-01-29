"""Comprehensive tests for verification endpoints."""

import pytest
from datetime import datetime, timezone, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

from app.models.verification import Verification
from app.models.user import User


class TestVerificationEndpoints:
    """Test verification endpoints comprehensively."""

    def test_get_available_services_success(self, client):
        """Test getting available services."""
        with patch("app.services.textverified_service.TextVerifiedService") as mock_tv:
            mock_instance = MagicMock()
            mock_instance.enabled = True
            mock_instance.get_services = AsyncMock(return_value={
                "services": [
                    {"name": "telegram", "price": 0.50},
                    {"name": "whatsapp", "price": 0.75}
                ]
            })
            mock_tv.return_value = mock_instance

            response = client.get("/api/v1/verify/services")
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert "services" in data
            assert data["total"] == 2

    def test_get_available_services_unavailable(self, client):
        """Test getting services when TextVerified is unavailable."""
        with patch("app.services.textverified_service.TextVerifiedService") as mock_tv:
            mock_instance = MagicMock()
            mock_instance.enabled = False
            mock_tv.return_value = mock_instance

            response = client.get("/api/v1/verify/services")
            assert response.status_code == 503
            # Response may have different structure, just check status code
            data = response.json()
            assert "detail" in data or "message" in data or "error" in data

    def test_create_verification_success(self, client, regular_user, db):
        """Test successful verification creation."""
        with patch("app.services.textverified_service.TextVerifiedService") as mock_tv:
            mock_instance = MagicMock()
            mock_instance.enabled = True
            mock_instance.create_verification = AsyncMock(return_value={
                "id": "tv-123",
                "phone_number": "+12025551234",
                "cost": 0.50
            })
            mock_tv.return_value = mock_instance

            with patch("app.core.dependencies.get_current_user_id", return_value=regular_user.id):
                response = client.post(
                    "/api/v1/verify/create",
                    json={
                        "service_name": "telegram",
                        "country": "US",
                        "capability": "sms"
                    }
                )

            assert response.status_code == 201
            data = response.json()
            assert "id" in data
            assert data["service_name"] == "telegram"
            assert data["phone_number"] == "+12025551234"
            assert data["status"] == "pending"

    def test_create_verification_insufficient_credits(self, client, regular_user, db):
        """Test verification creation with insufficient credits."""
        regular_user.credits = 0.0
        regular_user.free_verifications = 0
        db.commit()

        with patch("app.core.dependencies.get_current_user_id", return_value=regular_user.id):
            response = client.post(
                "/api/v1/verify/create",
                json={
                    "service_name": "telegram",
                    "country": "US",
                    "capability": "sms"
                }
            )

        assert response.status_code == 402
        assert "insufficient" in response.json()["detail"].lower()

    def test_create_verification_with_free_verifications(self, client, regular_user, db):
        """Test verification creation using free verifications."""
        regular_user.free_verifications = 5
        regular_user.credits = 0.0
        db.commit()

        with patch("app.services.textverified_service.TextVerifiedService") as mock_tv:
            mock_instance = MagicMock()
            mock_instance.enabled = True
            mock_instance.create_verification = AsyncMock(return_value={
                "id": "tv-123",
                "phone_number": "+12025551234",
                "cost": 0.50
            })
            mock_tv.return_value = mock_instance

            with patch("app.core.dependencies.get_current_user_id", return_value=regular_user.id):
                response = client.post(
                    "/api/v1/verify/create",
                    json={
                        "service_name": "telegram",
                        "country": "US",
                        "capability": "sms"
                    }
                )

            assert response.status_code == 201
            db.refresh(regular_user)
            assert regular_user.free_verifications == 4

    def test_create_verification_missing_service_name(self, client, regular_user):
        """Test verification creation without service name."""
        with patch("app.core.dependencies.get_current_user_id", return_value=regular_user.id):
            response = client.post(
                "/api/v1/verify/create",
                json={
                    "country": "US",
                    "capability": "sms"
                }
            )

        assert response.status_code == 422  # Validation error

    def test_create_verification_idempotency(self, client, regular_user, db):
        """Test idempotency key prevents duplicate verifications."""
        # Create first verification
        verification = Verification(
            user_id=regular_user.id,
            service_name="telegram",
            phone_number="+12025551234",
            status="pending",
            cost=0.50,
            capability="sms",
            country="US",
            idempotency_key="test-key-123",
            created_at=datetime.now(timezone.utc)
        )
        db.add(verification)
        db.commit()

        with patch("app.core.dependencies.get_current_user_id", return_value=regular_user.id):
            response = client.post(
                "/api/v1/verify/create",
                json={
                    "service_name": "telegram",
                    "country": "US",
                    "capability": "sms",
                    "idempotency_key": "test-key-123"
                }
            )

        assert response.status_code == 201
        data = response.json()
        assert data["id"] == verification.id

    def test_create_verification_with_area_code(self, client, payg_user, db):
        """Test verification creation with area code selection."""
        with patch("app.services.textverified_service.TextVerifiedService") as mock_tv:
            mock_instance = MagicMock()
            mock_instance.enabled = True
            mock_instance.create_verification = AsyncMock(return_value={
                "id": "tv-123",
                "phone_number": "+12025551234",
                "cost": 0.50
            })
            mock_tv.return_value = mock_instance

            with patch("app.core.dependencies.get_current_user_id", return_value=payg_user.id):
                response = client.post(
                    "/api/v1/verify/create",
                    json={
                        "service_name": "telegram",
                        "country": "US",
                        "capability": "sms",
                        "area_code": "202"
                    }
                )

            assert response.status_code == 201

    def test_create_verification_area_code_tier_restriction(self, client, regular_user):
        """Test area code selection requires PayG tier."""
        with patch("app.core.dependencies.get_current_user_id", return_value=regular_user.id):
            response = client.post(
                "/api/v1/verify/create",
                json={
                    "service_name": "telegram",
                    "country": "US",
                    "capability": "sms",
                    "area_code": "202"
                }
            )

        # Should fail due to tier restriction
        assert response.status_code in [402, 403]

    def test_create_verification_with_carrier(self, client, pro_user, db):
        """Test verification creation with carrier filtering."""
        with patch("app.services.textverified_service.TextVerifiedService") as mock_tv:
            mock_instance = MagicMock()
            mock_instance.enabled = True
            mock_instance.create_verification = AsyncMock(return_value={
                "id": "tv-123",
                "phone_number": "+12025551234",
                "cost": 0.50
            })
            mock_tv.return_value = mock_instance

            with patch("app.core.dependencies.get_current_user_id", return_value=pro_user.id):
                response = client.post(
                    "/api/v1/verify/create",
                    json={
                        "service_name": "telegram",
                        "country": "US",
                        "capability": "sms",
                        "carrier": "verizon"
                    }
                )

            assert response.status_code == 201

    def test_create_verification_carrier_tier_restriction(self, client, payg_user):
        """Test carrier filtering requires Pro tier."""
        with patch("app.core.dependencies.get_current_user_id", return_value=payg_user.id):
            response = client.post(
                "/api/v1/verify/create",
                json={
                    "service_name": "telegram",
                    "country": "US",
                    "capability": "sms",
                    "carrier": "verizon"
                }
            )

        # Should fail due to tier restriction
        assert response.status_code in [402, 403]

    def test_get_verification_status_success(self, client, regular_user, db):
        """Test getting verification status."""
        verification = Verification(
            user_id=regular_user.id,
            service_name="telegram",
            phone_number="+12025551234",
            status="pending",
            cost=0.50,
            capability="sms",
            country="US"
        )
        db.add(verification)
        db.commit()

        response = client.get(f"/api/v1/verify/{verification.id}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == verification.id
        assert data["status"] == "pending"
        assert data["phone_number"] == "+12025551234"

    def test_get_verification_status_not_found(self, client):
        """Test getting status for non-existent verification."""
        response = client.get("/api/v1/verify/nonexistent-id")
        assert response.status_code == 404

    def test_get_verification_history_success(self, client, regular_user, db):
        """Test getting verification history."""
        # Create multiple verifications
        for i in range(3):
            verification = Verification(
                user_id=regular_user.id,
                service_name=f"service{i}",
                phone_number=f"+1202555{i:04d}",
                status="completed",
                cost=0.50,
                capability="sms",
                country="US"
            )
            db.add(verification)
        db.commit()

        with patch("app.core.dependencies.get_current_user_id", return_value=regular_user.id):
            response = client.get("/api/v1/verify/history")

        assert response.status_code == 200
        data = response.json()
        assert "verifications" in data
        assert data["total_count"] == 3
        assert len(data["verifications"]) == 3

    def test_get_verification_history_pagination(self, client, regular_user, db):
        """Test verification history pagination."""
        # Create 10 verifications
        for i in range(10):
            verification = Verification(
                user_id=regular_user.id,
                service_name=f"service{i}",
                phone_number=f"+1202555{i:04d}",
                status="completed",
                cost=0.50,
                capability="sms",
                country="US"
            )
            db.add(verification)
        db.commit()

        with patch("app.core.dependencies.get_current_user_id", return_value=regular_user.id):
            response = client.get("/api/v1/verify/history?limit=5&offset=0")

        assert response.status_code == 200
        data = response.json()
        assert len(data["verifications"]) == 5
        assert data["total_count"] == 10

    def test_get_verification_history_empty(self, client, regular_user):
        """Test getting history when no verifications exist."""
        with patch("app.core.dependencies.get_current_user_id", return_value=regular_user.id):
            response = client.get("/api/v1/verify/history")

        assert response.status_code == 200
        data = response.json()
        assert data["total_count"] == 0
        assert len(data["verifications"]) == 0

    def test_get_verification_status_polling_pending(self, client, regular_user, db):
        """Test polling for pending verification."""
        verification = Verification(
            user_id=regular_user.id,
            service_name="telegram",
            phone_number="+12025551234",
            status="pending",
            cost=0.50,
            capability="sms",
            country="US",
            activation_id="tv-123"
        )
        db.add(verification)
        db.commit()

        with patch("app.services.textverified_service.TextVerifiedService") as mock_tv:
            mock_instance = MagicMock()
            mock_instance.get_sms = AsyncMock(return_value=None)
            mock_tv.return_value = mock_instance

            with patch("app.core.dependencies.get_current_user_id", return_value=regular_user.id):
                response = client.get(f"/api/v1/verify/{verification.id}/status")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "pending"
        assert data["sms_code"] is None

    def test_get_verification_status_polling_completed(self, client, regular_user, db):
        """Test polling when SMS is received."""
        verification = Verification(
            user_id=regular_user.id,
            service_name="telegram",
            phone_number="+12025551234",
            status="pending",
            cost=0.50,
            capability="sms",
            country="US",
            activation_id="tv-123"
        )
        db.add(verification)
        db.commit()

        with patch("app.services.textverified_service.TextVerifiedService") as mock_tv:
            mock_instance = MagicMock()
            mock_instance.get_sms = AsyncMock(return_value={
                "sms_code": "123456",
                "sms_text": "Your code is 123456"
            })
            mock_tv.return_value = mock_instance

            with patch("app.core.dependencies.get_current_user_id", return_value=regular_user.id):
                response = client.get(f"/api/v1/verify/{verification.id}/status")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "completed"
        assert data["sms_code"] == "123456"

    def test_get_verification_status_polling_not_found(self, client, regular_user):
        """Test polling for non-existent verification."""
        with patch("app.core.dependencies.get_current_user_id", return_value=regular_user.id):
            response = client.get("/api/v1/verify/nonexistent-id/status")

        assert response.status_code == 404

    def test_cancel_verification_success(self, client, regular_user, db):
        """Test canceling verification."""
        verification = Verification(
            user_id=regular_user.id,
            service_name="telegram",
            phone_number="+12025551234",
            status="pending",
            cost=0.50,
            capability="sms",
            country="US",
            activation_id="tv-123"
        )
        db.add(verification)
        db.commit()

        with patch("app.services.textverified_service.TextVerifiedService") as mock_tv:
            mock_instance = MagicMock()
            mock_instance.cancel_number = AsyncMock()
            mock_tv.return_value = mock_instance

            with patch("app.core.dependencies.get_current_user_id", return_value=regular_user.id):
                response = client.delete(f"/api/v1/verify/{verification.id}")

        assert response.status_code == 200
        db.refresh(verification)
        assert verification.status == "cancelled"

    def test_cancel_verification_not_found(self, client, regular_user):
        """Test canceling non-existent verification."""
        with patch("app.core.dependencies.get_current_user_id", return_value=regular_user.id):
            response = client.delete("/api/v1/verify/nonexistent-id")

        assert response.status_code == 404

    def test_cancel_verification_already_completed(self, client, regular_user, db):
        """Test canceling already completed verification."""
        verification = Verification(
            user_id=regular_user.id,
            service_name="telegram",
            phone_number="+12025551234",
            status="completed",
            cost=0.50,
            capability="sms",
            country="US",
            sms_code="123456"
        )
        db.add(verification)
        db.commit()

        with patch("app.core.dependencies.get_current_user_id", return_value=regular_user.id):
            response = client.delete(f"/api/v1/verify/{verification.id}")

        # Should still succeed but not call TextVerified
        assert response.status_code == 200
        db.refresh(verification)
        assert verification.status == "cancelled"

    def test_create_verification_service_unavailable(self, client, regular_user):
        """Test verification creation when service is unavailable."""
        with patch("app.services.textverified_service.TextVerifiedService") as mock_tv:
            mock_instance = MagicMock()
            mock_instance.enabled = False
            mock_tv.return_value = mock_instance

            with patch("app.core.dependencies.get_current_user_id", return_value=regular_user.id):
                response = client.post(
                    "/api/v1/verify/create",
                    json={
                        "service_name": "telegram",
                        "country": "US",
                        "capability": "sms"
                    }
                )

        assert response.status_code == 503

    def test_create_verification_user_not_found(self, client, db):
        """Test verification creation with non-existent user."""
        with patch("app.core.dependencies.get_current_user_id", return_value="nonexistent-user"):
            response = client.post(
                "/api/v1/verify/create",
                json={
                    "service_name": "telegram",
                    "country": "US",
                    "capability": "sms"
                }
            )

        assert response.status_code == 404
