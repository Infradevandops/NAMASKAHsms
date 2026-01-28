"""Integration tests for API endpoints."""

import pytest
from fastapi.testclient import TestClient


@pytest.mark.integration
def test_health_check(client: TestClient):
    """Test health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data


@pytest.mark.integration
def test_get_services_unauthorized(client: TestClient):
    """Test getting services without authentication."""
    response = client.get("/api/v1/verify/services")
    # Should either work (public endpoint) or return 401
    assert response.status_code in [200, 401]


@pytest.mark.integration
def test_get_history_with_auth(client: TestClient, auth_headers: dict):
    """Test getting verification history with authentication."""
    response = client.get(
        "/api/v1/verify/history?limit=50",
        headers=auth_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert "verifications" in data
    assert "total_count" in data
    assert isinstance(data["verifications"], list)


@pytest.mark.integration
def test_get_history_without_auth(client: TestClient):
    """Test getting verification history without authentication."""
    response = client.get("/api/v1/verify/history?limit=50")
    # Should return 401 or 403 without auth
    assert response.status_code in [401, 403]


@pytest.mark.integration
def test_diagnostics_endpoint(client: TestClient):
    """Test diagnostics endpoint."""
    response = client.get("/api/diagnostics")
    assert response.status_code == 200
    data = response.json()
    assert "timestamp" in data
    assert "environment" in data
    assert "version" in data
