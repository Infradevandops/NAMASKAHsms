"""Integration tests for onboarding wizard API (OB-20 to OB-23)."""

import uuid

import pytest
from fastapi.testclient import TestClient

from main import app

client = TestClient(app)

_TEST_EMAIL = "integration_onboarding@test.com"
_TEST_PASSWORD = "SecurePass123!"


def _get_token():
    client.post(
        "/api/auth/register",
        json={"email": _TEST_EMAIL, "password": _TEST_PASSWORD, "terms_accepted": True},
    )
    res = client.post(
        "/api/auth/login",
        json={"email": _TEST_EMAIL, "password": _TEST_PASSWORD},
    )
    return res.json().get("access_token")


def test_welcome_route_returns_200():
    """OB-20: GET /welcome returns 200 with no auth required."""
    response = client.get("/welcome")
    assert response.status_code == 200
    assert "Step 1 of 6" in response.text or "Welcome" in response.text


def test_onboarding_status_endpoint():
    """OB-21: authenticated GET returns correct shape."""
    token = _get_token()
    response = client.get(
        "/api/auth/onboarding-status",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "completed" in data
    assert "step" in data
    assert isinstance(data["completed"], bool)
    assert isinstance(data["step"], int)


def test_onboarding_complete_endpoint():
    """OB-22: authenticated PUT flips completed flag."""
    # Use a fresh user so state is clean
    unique_email = f"onboard_complete_{uuid.uuid4().hex[:8]}@test.com"
    client.post(
        "/api/auth/register",
        json={
            "email": unique_email,
            "password": _TEST_PASSWORD,
            "terms_accepted": True,
        },
    )
    res = client.post(
        "/api/auth/login",
        json={"email": unique_email, "password": _TEST_PASSWORD},
    )
    token = res.json().get("access_token")

    # Confirm not completed yet
    status_before = client.get(
        "/api/auth/onboarding-status",
        headers={"Authorization": f"Bearer {token}"},
    ).json()
    assert status_before["completed"] is False

    # Complete onboarding
    complete_res = client.put(
        "/api/auth/onboarding-complete",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert complete_res.status_code == 200
    assert complete_res.json() == {"status": "completed"}

    # Confirm flag flipped
    status_after = client.get(
        "/api/auth/onboarding-status",
        headers={"Authorization": f"Bearer {token}"},
    ).json()
    assert status_after["completed"] is True
    assert status_after["step"] == 6


def test_onboarding_complete_idempotent():
    """OB-23: calling PUT /onboarding-complete twice is safe."""
    unique_email = f"onboard_idem_{uuid.uuid4().hex[:8]}@test.com"
    client.post(
        "/api/auth/register",
        json={
            "email": unique_email,
            "password": _TEST_PASSWORD,
            "terms_accepted": True,
        },
    )
    res = client.post(
        "/api/auth/login",
        json={"email": unique_email, "password": _TEST_PASSWORD},
    )
    token = res.json().get("access_token")
    headers = {"Authorization": f"Bearer {token}"}

    r1 = client.put("/api/auth/onboarding-complete", headers=headers)
    r2 = client.put("/api/auth/onboarding-complete", headers=headers)

    assert r1.status_code == 200
    assert r2.status_code == 200
    assert r2.json() == {"status": "completed"}


def test_onboarding_status_requires_auth():
    """OB-18: unauthenticated GET returns 401/403."""
    response = client.get("/api/auth/onboarding-status")
    assert response.status_code in [401, 403]


def test_onboarding_complete_requires_auth():
    """OB-19: unauthenticated PUT returns 401/403."""
    response = client.put("/api/auth/onboarding-complete")
    assert response.status_code in [401, 403]


def test_register_returns_redirect_to_welcome():
    """Post-register response includes redirect=/welcome hint."""
    unique_email = f"onboard_reg_{uuid.uuid4().hex[:8]}@test.com"
    response = client.post(
        "/api/auth/register",
        json={
            "email": unique_email,
            "password": _TEST_PASSWORD,
            "terms_accepted": True,
        },
    )
    assert response.status_code in [200, 201]
    data = response.json()
    assert data.get("redirect") == "/welcome"


def test_onboarding_status_put_endpoint():
    """Verify authenticated PUT /api/auth/onboarding-status updates the user's step."""
    unique_email = f"onboard_put_{uuid.uuid4().hex[:8]}@test.com"
    client.post(
        "/api/auth/register",
        json={
            "email": unique_email,
            "password": _TEST_PASSWORD,
            "terms_accepted": True,
        },
    )
    res = client.post(
        "/api/auth/login",
        json={"email": unique_email, "password": _TEST_PASSWORD},
    )
    token = res.json().get("access_token")
    headers = {"Authorization": f"Bearer {token}"}

    # Update step to 3
    response = client.put(
        "/api/auth/onboarding-status", headers=headers, json={"step": 3}
    )
    assert response.status_code == 200
    assert response.json() == {"status": "success", "step": 3}

    # Verify updated step is persisted
    get_response = client.get("/api/auth/onboarding-status", headers=headers)
    assert get_response.status_code == 200
    assert get_response.json()["step"] == 3


def test_me_returns_tier():
    """Verify /api/auth/me returns the user's subscription tier."""
    token = _get_token()
    response = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    data = response.json()
    assert "tier" in data
    assert data["tier"] == "freemium"
