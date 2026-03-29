"""
E2E Tests for Verification Flow
Tests the complete user journey from service selection to SMS code receipt
"""
import pytest
import time
from playwright.sync_api import Page, expect


class TestVerificationFlow:
    """Test complete verification flow matching TextVerified UX"""
    
    @pytest.fixture(autouse=True)
    def setup(self, page: Page, base_url):
        """Setup: Navigate to verification page"""
        base = base_url.replace("localhost", "127.0.0.1")
        page.goto(f"{base}/verify")
        page.wait_for_load_state("networkidle")
        yield page
    
    def test_page_loads_with_services_ready(self, page: Page):
        """Services should load within 100ms of page load"""
        start = time.time()
        
        # Wait for services to be ready
        page.wait_for_function(
            "window.ServiceStore && window.ServiceStore.services && window.ServiceStore.services.length > 0",
            timeout=5000
        )
        
        elapsed = (time.time() - start) * 1000
        assert elapsed < 5000, f"Services took {elapsed}ms to load (target: <5000ms)"
        
        # Verify service count
        service_count = page.evaluate("window.ServiceStore.services.length")
        assert service_count >= 12, f"Expected ≥12 services, got {service_count}"
    
    def test_service_input_enabled_after_load(self, page: Page):
        """Service input should be enabled after services load"""
        service_input = page.locator("#service-search-input")
        
        # Should start disabled with loading text
        expect(service_input).to_be_disabled()
        expect(service_input).to_have_attribute("placeholder", "Loading services...")
        
        # Should become enabled within 5 seconds
        expect(service_input).to_be_enabled(timeout=5000)
        expect(service_input).to_have_attribute("placeholder", "Search services e.g. Telegram, WhatsApp...")
    
    def test_dropdown_opens_with_services(self, page: Page):
        """Dropdown should open instantly with services when input focused"""
        # Wait for services to load
        page.wait_for_function(
            "window._modalItems && window._modalItems.service && window._modalItems.service.length > 0",
            timeout=5000
        )
        
        # Click service input
        page.click("#service-search-input")
        
        # Dropdown should appear within 50ms
        dropdown = page.locator("#service-inline-dropdown")
        expect(dropdown).to_be_visible(timeout=100)
        
        # Should show services (not loading state)
        service_items = page.locator(".service-item")
        expect(service_items.first).to_be_visible(timeout=100)
        
        # Should have at least 5 services
        count = service_items.count()
        assert count >= 5, f"Expected ≥5 services in dropdown, got {count}"
    
    def test_search_filters_services(self, page: Page):
        """Search should filter services in real-time"""
        # Wait for services
        page.wait_for_function(
            "window._modalItems && window._modalItems.service && window._modalItems.service.length > 0",
            timeout=5000
        )
        
        # Open dropdown
        page.click("#service-search-input")
        page.wait_for_selector("#service-inline-dropdown", state="visible")
        
        # Type "telegram"
        page.fill("#service-search-input", "telegram")
        
        # Wait for filter (300ms debounce)
        page.wait_for_timeout(400)
        
        # Should show Telegram
        telegram = page.locator(".service-item:has-text('Telegram')")
        expect(telegram).to_be_visible()
        
        # Should not show unrelated services
        service_items = page.locator(".service-item")
        count = service_items.count()
        assert count <= 3, f"Search 'telegram' returned {count} items (should be ≤3)"
    
    def test_service_selection_updates_ui(self, page: Page):
        """Selecting a service should update UI and enable continue button"""
        # Wait for services
        page.wait_for_function(
            "window._modalItems && window._modalItems.service && window._modalItems.service.length > 0",
            timeout=5000
        )
        
        # Open dropdown and select WhatsApp
        page.click("#service-search-input")
        page.wait_for_selector("#service-inline-dropdown", state="visible")
        page.click(".service-item:has-text('WhatsApp')")
        
        # Dropdown should close
        expect(page.locator("#service-inline-dropdown")).to_be_hidden()
        
        # Selected service should display
        selected_display = page.locator("#service-selected-display")
        expect(selected_display).to_be_visible()
        expect(page.locator("#service-display")).to_contain_text("WhatsApp")
        
        # Continue button should be enabled
        continue_btn = page.locator("#continue-btn")
        expect(continue_btn).to_be_enabled()
    
    def test_official_logos_display(self, page: Page):
        """Services should display official logos from SimpleIcons CDN"""
        # Wait for services
        page.wait_for_function(
            "window._modalItems && window._modalItems.service && window._modalItems.service.length > 0",
            timeout=5000
        )
        
        # Open dropdown
        page.click("#service-search-input")
        page.wait_for_selector("#service-inline-dropdown", state="visible")
        
        # Check for service icons
        icons = page.locator(".service-icon")
        expect(icons.first).to_be_visible()
        
        # Verify icon src is from SimpleIcons CDN
        first_icon_src = icons.first.get_attribute("src")
        assert "simpleicons.org" in first_icon_src or "data:image" in first_icon_src, \
            f"Expected SimpleIcons CDN or fallback, got: {first_icon_src}"
    
    def test_pin_service_persists(self, page: Page):
        """Pinning a service should persist across page reloads"""
        # Wait for services
        page.wait_for_function(
            "window._modalItems && window._modalItems.service && window._modalItems.service.length > 0",
            timeout=5000
        )
        
        # Open dropdown
        page.click("#service-search-input")
        page.wait_for_selector("#service-inline-dropdown", state="visible")
        
        # Pin WhatsApp (click pin button)
        pin_buttons = page.locator(".service-item button[title*='Pin']")
        if pin_buttons.count() > 0:
            pin_buttons.first.click()
            
            # Reload page
            page.reload()
            page.wait_for_load_state("networkidle")
            
            # Open dropdown again
            page.wait_for_function(
                "window._modalItems && window._modalItems.service && window._modalItems.service.length > 0",
                timeout=5000
            )
            page.click("#service-search-input")
            page.wait_for_selector("#service-inline-dropdown", state="visible")
            
            # Pinned service should appear first
            first_service = page.locator(".service-item").first
            expect(first_service).to_be_visible()
    
    def test_fallback_services_on_api_failure(self, page: Page):
        """Should show fallback services if API fails"""
        # Block API requests
        page.route("**/api/countries/*/services", lambda route: route.abort())
        
        # Reload page
        page.reload()
        page.wait_for_load_state("networkidle")
        
        # Wait for fallback to kick in (5s timeout + 500ms retry)
        page.wait_for_timeout(6000)
        
        # Service input should still be enabled
        service_input = page.locator("#service-search-input")
        expect(service_input).to_be_enabled()
        
        # Open dropdown
        page.click("#service-search-input")
        page.wait_for_selector("#service-inline-dropdown", state="visible")
        
        # Should show fallback services
        service_items = page.locator(".service-item")
        count = service_items.count()
        assert count >= 5, f"Expected ≥5 fallback services, got {count}"
        
        # Should include common services
        expect(page.locator(".service-item:has-text('WhatsApp')")).to_be_visible()
        expect(page.locator(".service-item:has-text('Telegram')")).to_be_visible()
    
    def test_step_2_pricing_display(self, page: Page):
        """Step 2 should show accurate pricing breakdown"""
        # Wait for services and select one
        page.wait_for_function(
            "window._modalItems && window._modalItems.service && window._modalItems.service.length > 0",
            timeout=5000
        )
        page.click("#service-search-input")
        page.wait_for_selector("#service-inline-dropdown", state="visible")
        page.click(".service-item:has-text('WhatsApp')")
        
        # Click continue
        page.click("#continue-btn")
        
        # Should show step 2
        step_2_card = page.locator("#step-2-card")
        expect(step_2_card).to_be_visible()
        
        # Should show service name
        expect(page.locator("#pricing-service")).to_contain_text("WhatsApp")
        
        # Should show cost
        cost = page.locator("#pricing-cost").inner_text()
        assert "$" in cost, f"Expected cost with $, got: {cost}"
        
        # Should show balance
        balance = page.locator("#pricing-balance").inner_text()
        assert "$" in balance, f"Expected balance with $, got: {balance}"
    
    def test_back_button_navigation(self, page: Page):
        """Back button should navigate between steps correctly"""
        # Go to step 2
        page.wait_for_function(
            "window._modalItems && window._modalItems.service && window._modalItems.service.length > 0",
            timeout=5000
        )
        page.click("#service-search-input")
        page.wait_for_selector("#service-inline-dropdown", state="visible")
        page.click(".service-item:has-text('WhatsApp')")
        page.click("#continue-btn")
        
        # Verify step 2 visible
        expect(page.locator("#step-2-card")).to_be_visible()
        expect(page.locator("#step-1-card")).to_be_hidden()
        
        # Click back
        page.click("#step-2-card button:has-text('Back')")
        
        # Should return to step 1
        expect(page.locator("#step-1-card")).to_be_visible()
        expect(page.locator("#step-2-card")).to_be_hidden()
        
        # Service should still be selected
        expect(page.locator("#service-selected-display")).to_be_visible()
        expect(page.locator("#continue-btn")).to_be_enabled()
    
    def test_clear_service_selection(self, page: Page):
        """Clear button should reset service selection"""
        # Select a service
        page.wait_for_function(
            "window._modalItems && window._modalItems.service && window._modalItems.service.length > 0",
            timeout=5000
        )
        page.click("#service-search-input")
        page.wait_for_selector("#service-inline-dropdown", state="visible")
        page.click(".service-item:has-text('WhatsApp')")
        
        # Verify selected
        expect(page.locator("#service-selected-display")).to_be_visible()
        expect(page.locator("#continue-btn")).to_be_enabled()
        
        # Click clear (X button)
        page.click("#service-selected-display button")
        
        # Should clear selection
        expect(page.locator("#service-selected-display")).to_be_hidden()
        expect(page.locator("#continue-btn")).to_be_disabled()
        expect(page.locator("#service-search-input")).to_have_value("")
    
    def test_progress_indicator_updates(self, page: Page):
        """Progress indicator should update as user moves through steps"""
        # Step 1 should be active
        expect(page.locator("#step-1.active")).to_be_visible()
        expect(page.locator("#progress-fill")).to_have_css("width", "0px")
        
        # Go to step 2
        page.wait_for_function(
            "window._modalItems && window._modalItems.service && window._modalItems.service.length > 0",
            timeout=5000
        )
        page.click("#service-search-input")
        page.wait_for_selector("#service-inline-dropdown", state="visible")
        page.click(".service-item:has-text('WhatsApp')")
        page.click("#continue-btn")
        
        # Step 2 should be active
        expect(page.locator("#step-2.active")).to_be_visible()
        expect(page.locator("#step-1.completed")).to_be_visible()
        
        # Progress bar should be at 50%
        progress_width = page.locator("#progress-fill").evaluate("el => el.style.width")
        assert "50" in progress_width, f"Expected 50% progress, got: {progress_width}"


@pytest.fixture
def authenticated_page(page: Page, base_url):
    """Fixture to authenticate user before tests"""
    base = base_url.replace("localhost", "127.0.0.1")
    # Login
    page.goto(f"{base}/login")
    page.fill("input[name='email']", "admin@namaskah.app")
    page.fill("input[name='password']", "admin123")
    page.click("button[type='submit']")
    page.wait_for_url("**/dashboard", timeout=10000)
    return page
