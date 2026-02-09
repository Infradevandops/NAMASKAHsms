"""E2E tests for dashboard pages"""
import pytest
from playwright.sync_api import Page, expect

BASE_URL = "http://localhost:8000"

@pytest.fixture
def authenticated_page(page: Page):
    """Login and return authenticated page"""
    page.goto(f"{BASE_URL}/auth/login")
    page.fill('input[name="email"]', "test@example.com")
    page.fill('input[name="password"]', "testpass123")
    page.click('button[type="submit"]')
    expect(page).to_have_url(f"{BASE_URL}/dashboard", timeout=5000)
    return page

def test_dashboard_loads(authenticated_page: Page):
    """Test dashboard page loads without errors"""
    authenticated_page.goto(f"{BASE_URL}/dashboard")
    expect(authenticated_page.locator('text=Dashboard')).to_be_visible()
    expect(authenticated_page.locator('#balance-display')).to_be_visible()

def test_analytics_page_loads(authenticated_page: Page):
    """Test analytics page loads with charts"""
    authenticated_page.goto(f"{BASE_URL}/analytics")
    expect(authenticated_page.locator('text=Analytics')).to_be_visible()
    # Wait for charts to render
    authenticated_page.wait_for_timeout(2000)
    expect(authenticated_page.locator('#stats-grid')).to_be_visible()

def test_wallet_page_loads(authenticated_page: Page):
    """Test wallet page loads with balance"""
    authenticated_page.goto(f"{BASE_URL}/wallet")
    expect(authenticated_page.locator('text=Wallet')).to_be_visible()
    expect(authenticated_page.locator('#wallet-balance')).to_be_visible()

def test_history_page_loads(authenticated_page: Page):
    """Test history page loads"""
    authenticated_page.goto(f"{BASE_URL}/history")
    expect(authenticated_page.locator('text=History')).to_be_visible()
    expect(authenticated_page.locator('#history-body')).to_be_visible()

def test_notifications_page_loads(authenticated_page: Page):
    """Test notifications page loads"""
    authenticated_page.goto(f"{BASE_URL}/notifications")
    expect(authenticated_page.locator('text=Notifications')).to_be_visible()
    expect(authenticated_page.locator('#notification-list')).to_be_visible()

def test_settings_page_loads(authenticated_page: Page):
    """Test settings page loads with tabs"""
    authenticated_page.goto(f"{BASE_URL}/settings")
    expect(authenticated_page.locator('text=Settings')).to_be_visible()
    expect(authenticated_page.locator('#account-email')).to_be_visible()

def test_webhooks_page_loads(authenticated_page: Page):
    """Test webhooks page loads"""
    authenticated_page.goto(f"{BASE_URL}/webhooks")
    expect(authenticated_page.locator('text=Webhooks')).to_be_visible()

def test_referrals_page_loads(authenticated_page: Page):
    """Test referrals page loads"""
    authenticated_page.goto(f"{BASE_URL}/referrals")
    expect(authenticated_page.locator('text=Referral')).to_be_visible()
    expect(authenticated_page.locator('#referral-url')).to_be_visible()
