"""E2E Critical Path Tests - Smoke Tests for CI/CD"""

import pytest
from playwright.async_api import expect


@pytest.mark.asyncio
async def test_homepage_loads(page, base_url):
    """Test that homepage loads successfully."""
    await page.goto(base_url)
    await expect(page).to_have_title("Namaskah")


@pytest.mark.asyncio
async def test_registration_flow(page, base_url):
    """Test user registration flow."""
    await page.goto(f"{base_url}/register")
    await page.fill('input[name="email"]', "test@example.com")
    await page.fill('input[name="password"]', "SecurePass123!")
    await page.fill('input[name="confirm_password"]', "SecurePass123!")
    await page.click('button[type="submit"]')
    await expect(page).to_have_url(f"{base_url}/login", timeout=5000)


@pytest.mark.asyncio
async def test_login_flow(page, base_url):
    """Test user login flow."""
    await page.goto(f"{base_url}/login")
    await page.fill('input[name="email"]', "test@example.com")
    await page.fill('input[name="password"]', "SecurePass123!")
    await page.click('button[type="submit"]')
    await expect(page).to_have_url(f"{base_url}/dashboard", timeout=5000)


@pytest.mark.asyncio
async def test_health_endpoint(page, base_url):
    """Test health endpoint returns 200."""
    response = await page.goto(f"{base_url}/health")
    assert response.status == 200


@pytest.mark.asyncio
async def test_api_diagnostics(page, base_url):
    """Test diagnostics endpoint."""
    response = await page.goto(f"{base_url}/api/diagnostics")
    assert response.status == 200
    data = await response.json()
    assert "timestamp" in data
    assert "environment" in data
    assert "version" in data
