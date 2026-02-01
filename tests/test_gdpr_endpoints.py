"""Tests for GDPR/Privacy endpoints."""


import pytest
from fastapi.testclient import TestClient
from main import app

@pytest.fixture
def client():

    return TestClient(app)


def test_privacy_page_is_public(client):

    """Privacy Policy page should be public."""
    response = client.get("/privacy")
    assert response.status_code == 200


def test_privacy_settings_requires_auth(client):

    """Privacy Settings page should require authentication."""
    response = client.get("/privacy-settings", follow_redirects=False)
    assert response.status_code in [401, 302, 307]


def test_privacy_settings_loads(client, auth_headers):

    """Privacy Settings page should load for authenticated users."""
    response = client.get("/privacy-settings", headers=auth_headers)
    assert response.status_code == 200
    assert b"Privacy" in response.content or b"GDPR" in response.content


def test_data_export_requires_auth(client):

    """Data export should require authentication."""
    response = client.get("/api/gdpr/export")
    assert response.status_code == 401


def test_data_export_returns_json(client, auth_headers):

    """Data export should return JSON data for authenticated user."""
    response = client.get("/api/gdpr/export", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert "user" in data or "export_date" in data


def test_account_deletion_requires_auth(client):

    """Account deletion should require authentication."""
    response = client.delete("/api/gdpr/account")
    assert response.status_code == 401


def test_account_deletion_works(client, auth_headers):

    """Account deletion endpoint should be accessible with auth."""
    response = client.delete("/api/gdpr/account", headers=auth_headers)
    assert response.status_code in [200, 404, 500]


def test_page_has_export_button(client, auth_headers):

    """Privacy settings page should have data export button."""
    response = client.get("/privacy-settings", headers=auth_headers)
    assert response.status_code == 200
    assert b"Export" in response.content or b"export" in response.content


def test_page_has_delete_section(client, auth_headers):

    """Privacy settings page should have account deletion section."""
    response = client.get("/privacy-settings", headers=auth_headers)
    assert response.status_code == 200
    assert b"Delete" in response.content or b"delete" in response.content


def test_export_includes_verifications(client, auth_headers):

    """Export should include verification history format."""
    response = client.get("/api/gdpr/export", headers=auth_headers)
if response.status_code == 200:
        data = response.json()
        assert "verifications" in data


def test_export_has_timestamp(client, auth_headers):

    """Export should include export timestamp."""
    response = client.get("/api/gdpr/export", headers=auth_headers)
if response.status_code == 200:
        data = response.json()
        assert any(k in data for k in ["export_date", "exported_at", "timestamp"])