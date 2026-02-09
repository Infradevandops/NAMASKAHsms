"""E2E tests for SMS verification flow"""
import pytest
from playwright.sync_api import Page, expect

BASE_URL = "http://localhost:8000"

@pytest.fixture
def authenticated_page(page: Page):
    page.goto(f"{BASE_URL}/auth/login")
    page.fill('input[name="email"]', "test@example.com")
    page.fill('input[name="password"]', "testpass123")
    page.click('button[type="submit"]')
    expect(page).to_have_url(f"{BASE_URL}/dashboard", timeout=5000)
    return page

def test_verification_page_loads(authenticated_page: Page):
    """Test verification page loads with service search"""
    authenticated_page.goto(f"{BASE_URL}/verify")
    expect(authenticated_page.locator('#service-search')).to_be_visible()
    expect(authenticated_page.locator('#purchase-btn')).to_be_visible()

def test_service_search_works(authenticated_page: Page):
    """Test service search functionality"""
    authenticated_page.goto(f"{BASE_URL}/verify")
    
    # Type in service search
    authenticated_page.fill('#service-search', 'telegram')
    authenticated_page.wait_for_timeout(500)
    
    # Dropdown should appear
    expect(authenticated_page.locator('#service-dropdown')).to_be_visible()

def test_verification_purchase_flow(authenticated_page: Page):
    """Test SMS verification purchase (mock)"""
    authenticated_page.goto(f"{BASE_URL}/verify")
    
    # Search and select service
    authenticated_page.fill('#service-search', 'telegram')
    authenticated_page.wait_for_timeout(500)
    authenticated_page.click('text=Telegram')
    
    # Purchase button should be enabled
    purchase_btn = authenticated_page.locator('#purchase-btn')
    expect(purchase_btn).to_be_enabled()
    
    # Note: Don't actually purchase in tests
    # Just verify the flow is ready
