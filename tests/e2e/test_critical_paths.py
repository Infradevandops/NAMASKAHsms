"""
import pytest
from playwright.sync_api import Page, expect

E2E Critical Path Tests - Smoke Tests for CI/CD
"""


@pytest.fixture(scope="module")
def base_url():

    return "http://localhost:8000"


def test_homepage_loads(page: Page, base_url: str):

    """Test that homepage loads successfully."""
    page.goto(base_url)
    expect(page).to_have_title("Namaskah")


def test_registration_flow(page: Page, base_url: str):

    """Test user registration flow."""
    page.goto(f"{base_url}/register")

    # Fill registration form
    page.fill('input[name="email"]', "test@example.com")
    page.fill('input[name="password"]', "SecurePass123!")
    page.fill('input[name="confirm_password"]', "SecurePass123!")

    # Submit form
    page.click('button[type="submit"]')

    # Check for success or redirect
    expect(page).to_have_url(f"{base_url}/login", timeout=5000)


def test_login_flow(page: Page, base_url: str):

    """Test user login flow."""
    page.goto(f"{base_url}/login")

    # Fill login form
    page.fill('input[name="email"]', "test@example.com")
    page.fill('input[name="password"]', "SecurePass123!")

    # Submit
    page.click('button[type="submit"]')

    # Should redirect to dashboard
    expect(page).to_have_url(f"{base_url}/dashboard", timeout=5000)


def test_health_endpoint(page: Page, base_url: str):

    """Test health endpoint returns 200."""
    response = page.goto(f"{base_url}/health")
    assert response.status == 200


def test_api_diagnostics(page: Page, base_url: str):

    """Test diagnostics endpoint."""
    response = page.goto(f"{base_url}/api/diagnostics")
    assert response.status == 200

    # Check response contains expected fields
    data = response.json()
    assert "timestamp" in data
    assert "environment" in data
    assert "version" in data