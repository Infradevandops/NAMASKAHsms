"""E2E tests for dashboard pages"""

import pytest
from playwright.async_api import expect

BASE_URL = "http://localhost:8000"


@pytest.fixture
async def authenticated_page(page):
    """Login and return authenticated page"""
    await page.goto(f"{BASE_URL}/auth/login")
    await page.fill('input[name="email"]', "test@example.com")
    await page.fill('input[name="password"]', "testpass123")
    await page.click('button[type="submit"]')
    await expect(page).to_have_url(f"{BASE_URL}/dashboard", timeout=5000)
    return page


@pytest.mark.asyncio
async def test_dashboard_loads(authenticated_page):
    """Test dashboard page loads without errors"""
    await authenticated_page.goto(f"{BASE_URL}/dashboard")
    await expect(authenticated_page.locator("text=Dashboard")).to_be_visible()
    await expect(authenticated_page.locator("#balance-display")).to_be_visible()


@pytest.mark.asyncio
async def test_analytics_page_loads(authenticated_page):
    """Test analytics page loads with charts"""
    await authenticated_page.goto(f"{BASE_URL}/analytics")
    await expect(authenticated_page.locator("text=Analytics")).to_be_visible()
    await authenticated_page.wait_for_timeout(2000)
    await expect(authenticated_page.locator("#stats-grid")).to_be_visible()


@pytest.mark.asyncio
async def test_wallet_page_loads(authenticated_page):
    """Test wallet page loads with balance"""
    await authenticated_page.goto(f"{BASE_URL}/wallet")
    await expect(authenticated_page.locator("text=Wallet")).to_be_visible()
    await expect(authenticated_page.locator("#wallet-balance")).to_be_visible()


@pytest.mark.asyncio
async def test_history_page_loads(authenticated_page):
    """Test history page loads"""
    await authenticated_page.goto(f"{BASE_URL}/history")
    await expect(authenticated_page.locator("text=History")).to_be_visible()
    await expect(authenticated_page.locator("#history-body")).to_be_visible()


@pytest.mark.asyncio
async def test_notifications_page_loads(authenticated_page):
    """Test notifications page loads"""
    await authenticated_page.goto(f"{BASE_URL}/notifications")
    await expect(authenticated_page.locator("text=Notifications")).to_be_visible()
    await expect(authenticated_page.locator("#notification-list")).to_be_visible()


@pytest.mark.asyncio
async def test_settings_page_loads(authenticated_page):
    """Test settings page loads with tabs"""
    await authenticated_page.goto(f"{BASE_URL}/settings")
    await expect(authenticated_page.locator("text=Settings")).to_be_visible()
    await expect(authenticated_page.locator("#account-email")).to_be_visible()


@pytest.mark.asyncio
async def test_webhooks_page_loads(authenticated_page):
    """Test webhooks page loads"""
    await authenticated_page.goto(f"{BASE_URL}/webhooks")
    await expect(authenticated_page.locator("text=Webhooks")).to_be_visible()


@pytest.mark.asyncio
async def test_referrals_page_loads(authenticated_page):
    """Test referrals page loads"""
    await authenticated_page.goto(f"{BASE_URL}/referrals")
    await expect(authenticated_page.locator("text=Referral")).to_be_visible()
    await expect(authenticated_page.locator("#referral-url")).to_be_visible()
