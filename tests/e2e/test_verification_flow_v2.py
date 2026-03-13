"""
E2E Tests for Modernized Verification Flow (V2)
Tests the immersive modal UI, error handling, and fallback logic.
"""
import pytest
import time
from playwright.sync_api import Page, expect

@pytest.fixture(scope="function")
def page_manual(playwright):
    """Manually manage browser to avoid protocol errors"""
    browser = playwright.chromium.launch(headless=True)
    context = browser.new_context()
    page = context.new_page()
    yield page
    browser.close()

@pytest.fixture(autouse=True)
def authenticated_page(page_manual: Page, base_url):
    """Fixture to authenticate user and navigate to verification page before each test"""
    # Use base_url or default
    base = base_url if base_url else "http://127.0.0.1:8000"
    
    # Ensure base uses 127.0.0.1 if it's localhost
    base = base.replace("localhost", "127.0.0.1")
    
    # 1. Login
    page_manual.goto(f"{base}/login", timeout=15000)
    page_manual.fill("#email", "admin@namaskah.app")
    page_manual.fill("#password", "Namaskah@Admin2024")
    page_manual.click("button[type='submit']")
    page_manual.wait_for_url("**/dashboard", timeout=15000)
    
    # 2. Go to verification
    page_manual.goto(f"{base}/verify", timeout=15000)
    page_manual.wait_for_load_state("networkidle")
    return page_manual

def test_service_loading_error_and_retry(page_manual: Page):
    # Use page_manual instead of page
    page = page_manual
    """Test Case for Priority 0 & 1: API Failure -> Error State -> Retry -> Success"""
    
    # 1. Mock API to fail
    page.route("**/api/verification/services*", lambda route: route.fulfill(
        status=503,
        content_type="application/json",
        body='{"error": "Service unavailable"}'
    ))
    
    page.reload()
    page.wait_for_load_state("networkidle")
    
    # 2. Verify error state
    service_input = page.locator("#service-search-input")
    expect(service_input).to_be_disabled()
    expect(service_input).to_have_attribute("placeholder", "Services unavailable - please refresh page")
    
    # 3. Enable API and Retry
    page.route("**/api/verification/services*", lambda route: route.fulfill(
        status=200,
        content_type="application/json",
        body='{"services": [{"id": "telegram", "name": "Telegram", "price": 0.50}], "total": 1}'
    ))
    
    # Click service input (which should now be disabled, so we use evaluate to trigger retry if we added a button, 
    # but the task P1.3 says "Add error message with retry button in modal content")
    # Wait, the modal doesn't open if items are empty. 
    # Let's check the code: in openImmersiveModal it returns early.
    
    # Actually, Task 1.2 "Add retry button to the empty/error state' in the modal" 
    # suggests the modal SHOULD open even if empty? 
    # Click the actual retry button
    page.click("#service-retry-btn")
    
    # Verify recovered
    expect(service_input).to_be_enabled(timeout=15000)
    expect(service_input).to_have_attribute("placeholder", "Search services e.g. Telegram, WhatsApp...", timeout=10000)

def test_immersive_modal_opens(page_manual: Page):
    # Use page_manual
    page = page_manual
    """Test that clicking service selection opens the immersive modal"""
    # Wait for services
    page.wait_for_function(
        "window._modalItems && window._modalItems.service && window._modalItems.service.length > 0",
        timeout=20000
    )
    
    page.click("#service-search-input")
    
    modal = page.locator("#immersive-modal-container")
    expect(modal).not_to_be_empty()
    expect(page.locator(".immersive-modal-title")).to_have_text("Select Service")

def test_area_code_fallback_and_receipt(page_manual: Page):
    # Use page_manual
    page = page_manual
    """Test Case for Priority 1.5: Fallback warning and receipt accuracy"""
    
    # 1. Setup mocks for successful service loading
    page.route("**/api/verification/services*", lambda route: route.fulfill(
        status=200,
        content_type="application/json",
        body='{"services": [{"id": "telegram", "name": "Telegram", "price": 1.50}], "total": 1}'
    ))
    
    # 2. Mock purchase response WITH fallback
    page.route("**/api/verification/request", lambda route: route.fulfill(
        status=200,
        content_type="application/json",
        body='''{
            "success": true,
            "verification_id": "test_v_fallback",
            "phone_number": "14155550199",
            "carrier": "T-Mobile",
            "assigned_area_code": "415",
            "requested_area_code": "212",
            "fallback_applied": true,
            "same_state_fallback": false
        }'''
    ))
    
    # 3. Mock polling status to completed
    page.route("**/api/verification/status/*", lambda route: route.fulfill(
        status=200,
        content_type="application/json",
        body='''{
            "status": "completed",
            "sms_code": "123456",
            "assigned_carrier": "T-Mobile",
            "assigned_area_code": "415",
            "fallback_applied": true,
            "requested_area_code": "212"
        }'''
    ))
    
    # 4. Perform flow
    page.click("#service-search-input")
    page.wait_for_selector(".list-item", state="visible")
    page.click(".list-item:has-text('Telegram')")
    
    page.click("#continue-btn")
    page.click("#get-number-btn")
    
    # 5. Verify Fallback Warning shown in Step 3
    warning = page.locator("#fallback-warning")
    expect(warning).to_be_visible()
    expect(warning).to_contain_text("212 unavailable")
    
    # 6. Verify Receipt Details
    page.wait_for_selector("#code-received", state="visible", timeout=10000)
    
    expect(page.locator("#receipt-carrier")).to_have_text("T-Mobile")
    expect(page.locator("#receipt-area-code")).to_have_text("415")
    expect(page.locator("#receipt-fallback-row")).to_be_visible()
    expect(page.locator("#receipt-requested-ac")).to_have_text("212")

def test_carrier_mismatch_error(page_manual: Page):
    # Use page_manual
    page = page_manual
    """Test Case for Priority 2.3: Carrier mismatch raises 409 and shown to user"""
    
    # 1. Mock purchase failure with 409
    page.route("**/api/verification/request", lambda route: route.fulfill(
        status=409,
        content_type="application/json",
        body='{"detail": "Requested carrier Verizon was unavailable. Got T-Mobile. Verification cancelled."}'
    ))
    
    # 2. Select service and proceed
    page.wait_for_function("window._modalItems && window._modalItems.service && window._modalItems.service.length > 0")
    page.click("#service-search-input")
    page.click(".list-item:has-text('Telegram')")
    page.click("#continue-btn")
    
    # 3. Click Get Number
    page.click("#get-number-btn")
    
    # 4. Verify Error Toast or Message
    # In my JS, it catches error and shows window.toast.error(msg)
    # Give it more time for the toast to appear
    expect(page.locator(".toast-error")).to_contain_text("Requested carrier Verizon was unavailable", timeout=15000)


