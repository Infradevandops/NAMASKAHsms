"""E2E tests for authentication flows"""
import pytest
from playwright.sync_api import Page, expect

BASE_URL = "http://localhost:8000"

@pytest.fixture
def test_user():
    return {
        "email": "test_e2e@example.com",
        "password": "TestPass123!",
        "name": "E2E Test User"
    }

def test_registration_flow(page: Page, test_user):
    """Test user registration end-to-end"""
    page.goto(f"{BASE_URL}/auth/register")
    
    # Fill registration form
    page.fill('input[name="email"]', test_user["email"])
    page.fill('input[name="password"]', test_user["password"])
    page.fill('input[name="confirm_password"]', test_user["password"])
    
    # Submit form
    page.click('button[type="submit"]')
    
    # Should redirect to dashboard or login
    expect(page).to_have_url(f"{BASE_URL}/dashboard", timeout=5000)

def test_login_logout_flow(page: Page, test_user):
    """Test login and logout flow"""
    # Login
    page.goto(f"{BASE_URL}/auth/login")
    page.fill('input[name="email"]', test_user["email"])
    page.fill('input[name="password"]', test_user["password"])
    page.click('button[type="submit"]')
    
    # Verify dashboard loaded
    expect(page).to_have_url(f"{BASE_URL}/dashboard", timeout=5000)
    expect(page.locator('text=Dashboard')).to_be_visible()
    
    # Logout
    page.click('#user-avatar-btn')
    page.click('#dropdown-logout')
    
    # Should redirect to login
    expect(page).to_have_url(f"{BASE_URL}/auth/login", timeout=5000)

def test_password_reset_flow(page: Page, test_user):
    """Test password reset request"""
    page.goto(f"{BASE_URL}/auth/password-reset")
    page.fill('input[name="email"]', test_user["email"])
    page.click('button[type="submit"]')
    
    # Should show success message
    expect(page.locator('text=email sent')).to_be_visible(timeout=3000)
