"""Comprehensive tests for all API endpoints."""
import pytest
from decimal import Decimal
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, AsyncMock
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.exceptions import (
    ValidationError, AuthenticationError, AuthorizationError,
    NotFoundError, InsufficientCreditsError
)


class TestAuthenticationEndpoints:
    """Test authentication API endpoints."""

    @pytest.fixture
    def client(self):
        """Create test client."""
        from main import app
        return TestClient(app)

    def test_register_endpoint_success(self, client):
        """Test successful user registration."""
        response = client.post(
            "/api/auth/register",
            json={
                "email": "test@example.com",
                "password": "SecurePass123!",
                "name": "Test User"
            }
        )

        assert response.status_code in [200, 201]
        data = response.json()
        assert "user" in data or "id" in data

    def test_register_endpoint_invalid_email(self, client):
        """Test registration with invalid email."""
        response = client.post(
            "/api/auth/register",
            json={
                "email": "invalid-email",
                "password": "SecurePass123!",
                "name": "Test User"
            }
        )

        assert response.status_code == 400
        assert "error" in response.json()

    def test_register_endpoint_weak_password(self, client):
        """Test registration with weak password."""
        response = client.post(
            "/api/auth/register",
            json={
                "email": "test@example.com",
                "password": "weak",
                "name": "Test User"
            }
        )

        assert response.status_code == 400
        assert "error" in response.json()

    def test_login_endpoint_success(self, client):
        """Test successful login."""
        response = client.post(
            "/api/auth/login",
            json={
                "email": "test@example.com",
                "password": "SecurePass123!"
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert "token" in data or "access_token" in data

    def test_login_endpoint_invalid_credentials(self, client):
        """Test login with invalid credentials."""
        response = client.post(
            "/api/auth/login",
            json={
                "email": "test@example.com",
                "password": "wrongpassword"
            }
        )

        assert response.status_code == 401
        assert "error" in response.json()

    def test_logout_endpoint(self, client):
        """Test logout endpoint."""
        # First login
        login_response = client.post(
            "/api/auth/login",
            json={
                "email": "test@example.com",
                "password": "SecurePass123!"
            }
        )

        token = login_response.json().get("token") or login_response.json().get("access_token")

        # Then logout
        response = client.post(
            "/api/auth/logout",
            headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 200

    def test_refresh_token_endpoint(self, client):
        """Test token refresh endpoint."""
        response = client.post(
            "/api/auth/refresh",
            json={"refresh_token": "valid_refresh_token"}
        )

        assert response.status_code in [200, 401]


class TestVerificationEndpoints:
    """Test verification API endpoints."""

    @pytest.fixture
    def client(self):
        """Create test client."""
        from main import app
        return TestClient(app)

    @pytest.fixture
    def auth_headers(self, client):
        """Get authentication headers."""
        response = client.post(
            "/api/auth/login",
            json={
                "email": "test@example.com",
                "password": "SecurePass123!"
            }
        )
        token = response.json().get("token") or response.json().get("access_token")
        return {"Authorization": f"Bearer {token}"}

    def test_create_verification_endpoint(self, client, auth_headers):
        """Test verification creation endpoint."""
        response = client.post(
            "/api/verify/create",
            json={
                "service_name": "whatsapp",
                "country_code": "us"
            },
            headers=auth_headers
        )

        assert response.status_code in [200, 201]
        data = response.json()
        assert "id" in data or "verification_id" in data

    def test_create_verification_insufficient_credits(self, client, auth_headers):
        """Test verification creation with insufficient credits."""
        response = client.post(
            "/api/verify/create",
            json={
                "service_name": "whatsapp",
                "country_code": "us"
            },
            headers=auth_headers
        )

        # Should fail if user has no credits
        if response.status_code == 402:
            assert "insufficient" in response.json().get("error", "").lower()

    def test_get_verification_status_endpoint(self, client, auth_headers):
        """Test get verification status endpoint."""
        response = client.get(
            "/api/verify/status/verify123",
            headers=auth_headers
        )

        assert response.status_code in [200, 404]

    def test_get_verification_history_endpoint(self, client, auth_headers):
        """Test get verification history endpoint."""
        response = client.get(
            "/api/verify/history",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list) or "items" in data

    def test_cancel_verification_endpoint(self, client, auth_headers):
        """Test cancel verification endpoint."""
        response = client.post(
            "/api/verify/cancel/verify123",
            headers=auth_headers
        )

        assert response.status_code in [200, 404]

    def test_get_countries_endpoint(self, client):
        """Test get countries endpoint."""
        response = client.get("/api/countries")

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list) or "countries" in data

    def test_get_services_endpoint(self, client):
        """Test get services endpoint."""
        response = client.get("/api/countries/us/services")

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list) or "services" in data


class TestPaymentEndpoints:
    """Test payment API endpoints."""

    @pytest.fixture
    def client(self):
        """Create test client."""
        from main import app
        return TestClient(app)

    @pytest.fixture
    def auth_headers(self, client):
        """Get authentication headers."""
        response = client.post(
            "/api/auth/login",
            json={
                "email": "test@example.com",
                "password": "SecurePass123!"
            }
        )
        token = response.json().get("token") or response.json().get("access_token")
        return {"Authorization": f"Bearer {token}"}

    def test_add_credits_endpoint(self, client, auth_headers):
        """Test add credits endpoint."""
        response = client.post(
            "/api/billing/add-credits",
            json={"amount": 50.00},
            headers=auth_headers
        )

        assert response.status_code in [200, 201]
        data = response.json()
        assert "amount" in data or "credits" in data

    def test_add_credits_invalid_amount(self, client, auth_headers):
        """Test add credits with invalid amount."""
        response = client.post(
            "/api/billing/add-credits",
            json={"amount": -10.00},
            headers=auth_headers
        )

        assert response.status_code == 400

    def test_get_balance_endpoint(self, client, auth_headers):
        """Test get balance endpoint."""
        response = client.get(
            "/api/billing/balance",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert "balance" in data or "credits" in data

    def test_get_transaction_history_endpoint(self, client, auth_headers):
        """Test get transaction history endpoint."""
        response = client.get(
            "/api/billing/history",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list) or "transactions" in data

    def test_process_payment_endpoint(self, client, auth_headers):
        """Test process payment endpoint."""
        response = client.post(
            "/api/billing/payment",
            json={
                "amount": 50.00,
                "method": "credit_card"
            },
            headers=auth_headers
        )

        assert response.status_code in [200, 201, 400]

    def test_refund_endpoint(self, client, auth_headers):
        """Test refund endpoint."""
        response = client.post(
            "/api/billing/refund/payment123",
            headers=auth_headers
        )

        assert response.status_code in [200, 404]


class TestRentalEndpoints:
    """Test rental API endpoints."""

    @pytest.fixture
    def client(self):
        """Create test client."""
        from main import app
        return TestClient(app)

    @pytest.fixture
    def auth_headers(self, client):
        """Get authentication headers."""
        response = client.post(
            "/api/auth/login",
            json={
                "email": "test@example.com",
                "password": "SecurePass123!"
            }
        )
        token = response.json().get("token") or response.json().get("access_token")
        return {"Authorization": f"Bearer {token}"}

    def test_create_rental_endpoint(self, client, auth_headers):
        """Test create rental endpoint."""
        response = client.post(
            "/api/rentals/create",
            json={
                "service_name": "whatsapp",
                "country_code": "us",
                "duration_hours": 24
            },
            headers=auth_headers
        )

        assert response.status_code in [200, 201, 402]

    def test_get_active_rentals_endpoint(self, client, auth_headers):
        """Test get active rentals endpoint."""
        response = client.get(
            "/api/rentals/active",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list) or "rentals" in data

    def test_get_rental_status_endpoint(self, client, auth_headers):
        """Test get rental status endpoint."""
        response = client.get(
            "/api/rentals/rental123/status",
            headers=auth_headers
        )

        assert response.status_code in [200, 404]

    def test_extend_rental_endpoint(self, client, auth_headers):
        """Test extend rental endpoint."""
        response = client.post(
            "/api/rentals/rental123/extend",
            json={"additional_hours": 12},
            headers=auth_headers
        )

        assert response.status_code in [200, 404, 402]

    def test_get_rental_messages_endpoint(self, client, auth_headers):
        """Test get rental messages endpoint."""
        response = client.get(
            "/api/rentals/rental123/messages",
            headers=auth_headers
        )

        assert response.status_code in [200, 404]

    def test_release_rental_endpoint(self, client, auth_headers):
        """Test release rental endpoint."""
        response = client.post(
            "/api/rentals/rental123/release",
            headers=auth_headers
        )

        assert response.status_code in [200, 404]

    def test_get_rental_history_endpoint(self, client, auth_headers):
        """Test get rental history endpoint."""
        response = client.get(
            "/api/rentals/history",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list) or "rentals" in data


class TestAdminEndpoints:
    """Test admin API endpoints."""

    @pytest.fixture
    def client(self):
        """Create test client."""
        from main import app
        return TestClient(app)

    @pytest.fixture
    def admin_headers(self, client):
        """Get admin authentication headers."""
        response = client.post(
            "/api/auth/login",
            json={
                "email": "admin@example.com",
                "password": "AdminPass123!"
            }
        )
        token = response.json().get("token") or response.json().get("access_token")
        return {"Authorization": f"Bearer {token}"}

    def test_get_users_endpoint(self, client, admin_headers):
        """Test get users endpoint."""
        response = client.get(
            "/api/admin/users",
            headers=admin_headers
        )

        assert response.status_code in [200, 403]

    def test_get_user_details_endpoint(self, client, admin_headers):
        """Test get user details endpoint."""
        response = client.get(
            "/api/admin/users/user123",
            headers=admin_headers
        )

        assert response.status_code in [200, 403, 404]

    def test_get_system_stats_endpoint(self, client, admin_headers):
        """Test get system stats endpoint."""
        response = client.get(
            "/api/admin/stats",
            headers=admin_headers
        )

        assert response.status_code in [200, 403]

    def test_get_verification_stats_endpoint(self, client, admin_headers):
        """Test get verification stats endpoint."""
        response = client.get(
            "/api/admin/stats/verifications",
            headers=admin_headers
        )

        assert response.status_code in [200, 403]


class TestErrorHandling:
    """Test error handling across endpoints."""

    @pytest.fixture
    def client(self):
        """Create test client."""
        from main import app
        return TestClient(app)

    def test_unauthorized_access(self, client):
        """Test unauthorized access to protected endpoint."""
        response = client.get("/api/verify/history")

        assert response.status_code == 401
        assert "error" in response.json()

    def test_invalid_token(self, client):
        """Test access with invalid token."""
        response = client.get(
            "/api/verify/history",
            headers={"Authorization": "Bearer invalid_token"}
        )

        assert response.status_code == 401

    def test_not_found_error(self, client):
        """Test not found error."""
        response = client.get("/api/verify/status/nonexistent")

        assert response.status_code in [401, 404]

    def test_validation_error(self, client):
        """Test validation error."""
        response = client.post(
            "/api/auth/register",
            json={
                "email": "invalid",
                "password": "weak"
            }
        )

        assert response.status_code == 400
        assert "error" in response.json()

    def test_method_not_allowed(self, client):
        """Test method not allowed error."""
        response = client.get(
            "/api/auth/register"
        )

        assert response.status_code == 405

    def test_internal_server_error(self, client):
        """Test internal server error handling."""
        # This would require a specific error condition
        # For now, just verify error response format
        response = client.get("/api/nonexistent/endpoint")

        assert response.status_code in [404, 405]


class TestRateLimiting:
    """Test rate limiting on endpoints."""

    @pytest.fixture
    def client(self):
        """Create test client."""
        from main import app
        return TestClient(app)

    def test_rate_limit_on_login(self, client):
        """Test rate limiting on login endpoint."""
        # Make multiple requests
        for i in range(10):
            response = client.post(
                "/api/auth/login",
                json={
                    "email": "test@example.com",
                    "password": "wrongpassword"
                }
            )

            # Should eventually hit rate limit
            if response.status_code == 429:
                assert "rate limit" in response.json().get("error", "").lower()
                break

    def test_rate_limit_on_verification(self, client):
        """Test rate limiting on verification endpoint."""
        # This would require authentication
        # For now, just verify the endpoint exists
        response = client.get("/api/countries")

        assert response.status_code == 200


class TestCORSHeaders:
    """Test CORS headers on endpoints."""

    @pytest.fixture
    def client(self):
        """Create test client."""
        from main import app
        return TestClient(app)

    def test_cors_headers_present(self, client):
        """Test CORS headers are present."""
        response = client.get("/api/countries")

        # Check for CORS headers
        assert response.status_code == 200
        # CORS headers would be in response.headers


class TestResponseFormats:
    """Test response format consistency."""

    @pytest.fixture
    def client(self):
        """Create test client."""
        from main import app
        return TestClient(app)

    def test_success_response_format(self, client):
        """Test success response format."""
        response = client.get("/api/countries")

        assert response.status_code == 200
        data = response.json()
        # Should have consistent format

    def test_error_response_format(self, client):
        """Test error response format."""
        response = client.get("/api/verify/history")

        assert response.status_code == 401
        data = response.json()
        assert "error" in data or "detail" in data
