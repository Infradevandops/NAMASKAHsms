"""E2E tests for authentication flows"""

import pytest
from playwright.async_api import Page, expect

BASE_URL = "http://localhost:8000"


@pytest.fixture
def test_user():
    return {
        "email": "test_e2e@example.com",
        "password": "TestPass123!",
        "name": "E2E Test User",
    }


@pytest.mark.asyncio
async def test_registration_flow(page: Page, test_user):
    """Test user registration end-to-end"""
    await page.goto(f"{BASE_URL}/auth/register")

    # Fill registration form
    await page.fill('input[name="email"]', test_user["email"])
    await page.fill('input[name="password"]', test_user["password"])
    await page.fill('input[name="confirm_password"]', test_user["password"])

    # Submit form
    await page.click('button[type="submit"]')

    # Should redirect to dashboard or login
    await expect(page).to_have_url(f"{BASE_URL}/dashboard", timeout=5000)


@pytest.mark.asyncio
async def test_login_logout_flow(page: Page, test_user):
    """Test login and logout flow"""
    # Login
    await page.goto(f"{BASE_URL}/auth/login")
    await page.fill('input[name="email"]', test_user["email"])
    await page.fill('input[name="password"]', test_user["password"])
    await page.click('button[type="submit"]')

    # Verify dashboard loaded
    await expect(page).to_have_url(f"{BASE_URL}/dashboard", timeout=5000)
    await expect(page.locator("text=Dashboard")).to_be_visible()

    # Logout
    await page.click("#user-avatar-btn")
    await page.click("#dropdown-logout")

    # Should redirect to login
    await expect(page).to_have_url(f"{BASE_URL}/auth/login", timeout=5000)


@pytest.mark.asyncio
async def test_password_reset_flow(page: Page, test_user):
    """Test password reset request"""
    await page.goto(f"{BASE_URL}/auth/password-reset")
    await page.fill('input[name="email"]', test_user["email"])
    await page.click('button[type="submit"]')

    # Should show success message
    await expect(page.locator("text=email sent")).to_be_visible(timeout=3000)
