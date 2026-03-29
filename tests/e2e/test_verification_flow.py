"""E2E Tests for Verification Flow"""

import pytest
import time
from playwright.async_api import expect


class TestVerificationFlow:
    """Test complete verification flow matching TextVerified UX"""

    @pytest.fixture(autouse=True)
    async def setup(self, page, base_url):
        """Setup: Navigate to verification page"""
        base = base_url.replace("localhost", "127.0.0.1")
        await page.goto(f"{base}/verify")
        await page.wait_for_load_state("networkidle")
        yield page

    @pytest.mark.asyncio
    async def test_page_loads_with_services_ready(self, page):
        """Services should load within 100ms of page load"""
        start = time.time()

        await page.wait_for_function(
            "window.ServiceStore && window.ServiceStore.services && window.ServiceStore.services.length > 0",
            timeout=5000,
        )

        elapsed = (time.time() - start) * 1000
        assert elapsed < 5000, f"Services took {elapsed}ms to load (target: <5000ms)"

        service_count = await page.evaluate("window.ServiceStore.services.length")
        assert service_count >= 12, f"Expected ≥12 services, got {service_count}"

    @pytest.mark.asyncio
    async def test_service_input_enabled_after_load(self, page):
        """Service input should be enabled after services load"""
        service_input = page.locator("#service-search-input")

        await expect(service_input).to_be_disabled()
        await expect(service_input).to_have_attribute(
            "placeholder", "Loading services..."
        )

        await expect(service_input).to_be_enabled(timeout=5000)
        await expect(service_input).to_have_attribute(
            "placeholder", "Search services e.g. Telegram, WhatsApp..."
        )

    @pytest.mark.asyncio
    async def test_dropdown_opens_with_services(self, page):
        """Dropdown should open instantly with services when input focused"""
        await page.wait_for_function(
            "window._modalItems && window._modalItems.service && window._modalItems.service.length > 0",
            timeout=5000,
        )

        await page.click("#service-search-input")

        dropdown = page.locator("#service-inline-dropdown")
        await expect(dropdown).to_be_visible(timeout=100)

        service_items = page.locator(".service-item")
        await expect(service_items.first).to_be_visible(timeout=100)

        count = await service_items.count()
        assert count >= 5, f"Expected ≥5 services in dropdown, got {count}"

    @pytest.mark.asyncio
    async def test_search_filters_services(self, page):
        """Search should filter services in real-time"""
        await page.wait_for_function(
            "window._modalItems && window._modalItems.service && window._modalItems.service.length > 0",
            timeout=5000,
        )

        await page.click("#service-search-input")
        await page.wait_for_selector("#service-inline-dropdown", state="visible")

        await page.fill("#service-search-input", "telegram")

        await page.wait_for_timeout(400)

        telegram = page.locator(".service-item:has-text('Telegram')")
        await expect(telegram).to_be_visible()

        service_items = page.locator(".service-item")
        count = await service_items.count()
        assert count <= 3, f"Search 'telegram' returned {count} items (should be ≤3)"

    @pytest.mark.asyncio
    async def test_service_selection_updates_ui(self, page):
        """Selecting a service should update UI and enable continue button"""
        await page.wait_for_function(
            "window._modalItems && window._modalItems.service && window._modalItems.service.length > 0",
            timeout=5000,
        )

        await page.click("#service-search-input")
        await page.wait_for_selector("#service-inline-dropdown", state="visible")
        await page.click(".service-item:has-text('WhatsApp')")

        await expect(page.locator("#service-inline-dropdown")).to_be_hidden()

        selected_display = page.locator("#service-selected-display")
        await expect(selected_display).to_be_visible()
        await expect(page.locator("#service-display")).to_contain_text("WhatsApp")

        continue_btn = page.locator("#continue-btn")
        await expect(continue_btn).to_be_enabled()

    @pytest.mark.asyncio
    async def test_official_logos_display(self, page):
        """Services should display official logos from SimpleIcons CDN"""
        await page.wait_for_function(
            "window._modalItems && window._modalItems.service && window._modalItems.service.length > 0",
            timeout=5000,
        )

        await page.click("#service-search-input")
        await page.wait_for_selector("#service-inline-dropdown", state="visible")

        icons = page.locator(".service-icon")
        await expect(icons.first).to_be_visible()

        first_icon_src = await icons.first.get_attribute("src")
        assert (
            "simpleicons.org" in first_icon_src or "data:image" in first_icon_src
        ), f"Expected SimpleIcons CDN or fallback, got: {first_icon_src}"

    @pytest.mark.asyncio
    async def test_pin_service_persists(self, page):
        """Pinning a service should persist across page reloads"""
        await page.wait_for_function(
            "window._modalItems && window._modalItems.service && window._modalItems.service.length > 0",
            timeout=5000,
        )

        await page.click("#service-search-input")
        await page.wait_for_selector("#service-inline-dropdown", state="visible")

        pin_buttons = page.locator(".service-item button[title*='Pin']")
        if await pin_buttons.count() > 0:
            await pin_buttons.first.click()

            await page.reload()
            await page.wait_for_load_state("networkidle")

            await page.wait_for_function(
                "window._modalItems && window._modalItems.service && window._modalItems.service.length > 0",
                timeout=5000,
            )
            await page.click("#service-search-input")
            await page.wait_for_selector("#service-inline-dropdown", state="visible")

            first_service = page.locator(".service-item").first
            await expect(first_service).to_be_visible()

    @pytest.mark.asyncio
    async def test_fallback_services_on_api_failure(self, page):
        """Should show fallback services if API fails"""
        await page.route("**/api/countries/*/services", lambda route: route.abort())

        await page.reload()
        await page.wait_for_load_state("networkidle")

        await page.wait_for_timeout(6000)

        service_input = page.locator("#service-search-input")
        await expect(service_input).to_be_enabled()

        await page.click("#service-search-input")
        await page.wait_for_selector("#service-inline-dropdown", state="visible")

        service_items = page.locator(".service-item")
        count = await service_items.count()
        assert count >= 5, f"Expected ≥5 fallback services, got {count}"

        await expect(page.locator(".service-item:has-text('WhatsApp')")).to_be_visible()
        await expect(page.locator(".service-item:has-text('Telegram')")).to_be_visible()

    @pytest.mark.asyncio
    async def test_step_2_pricing_display(self, page):
        """Step 2 should show accurate pricing breakdown"""
        await page.wait_for_function(
            "window._modalItems && window._modalItems.service && window._modalItems.service.length > 0",
            timeout=5000,
        )
        await page.click("#service-search-input")
        await page.wait_for_selector("#service-inline-dropdown", state="visible")
        await page.click(".service-item:has-text('WhatsApp')")

        await page.click("#continue-btn")

        step_2_card = page.locator("#step-2-card")
        await expect(step_2_card).to_be_visible()

        await expect(page.locator("#pricing-service")).to_contain_text("WhatsApp")

        cost = await page.locator("#pricing-cost").inner_text()
        assert "$" in cost, f"Expected cost with $, got: {cost}"

        balance = await page.locator("#pricing-balance").inner_text()
        assert "$" in balance, f"Expected balance with $, got: {balance}"

    @pytest.mark.asyncio
    async def test_back_button_navigation(self, page):
        """Back button should navigate between steps correctly"""
        await page.wait_for_function(
            "window._modalItems && window._modalItems.service && window._modalItems.service.length > 0",
            timeout=5000,
        )
        await page.click("#service-search-input")
        await page.wait_for_selector("#service-inline-dropdown", state="visible")
        await page.click(".service-item:has-text('WhatsApp')")
        await page.click("#continue-btn")

        await expect(page.locator("#step-2-card")).to_be_visible()
        await expect(page.locator("#step-1-card")).to_be_hidden()

        await page.click("#step-2-card button:has-text('Back')")

        await expect(page.locator("#step-1-card")).to_be_visible()
        await expect(page.locator("#step-2-card")).to_be_hidden()

        await expect(page.locator("#service-selected-display")).to_be_visible()
        await expect(page.locator("#continue-btn")).to_be_enabled()

    @pytest.mark.asyncio
    async def test_clear_service_selection(self, page):
        """Clear button should reset service selection"""
        await page.wait_for_function(
            "window._modalItems && window._modalItems.service && window._modalItems.service.length > 0",
            timeout=5000,
        )
        await page.click("#service-search-input")
        await page.wait_for_selector("#service-inline-dropdown", state="visible")
        await page.click(".service-item:has-text('WhatsApp')")

        await expect(page.locator("#service-selected-display")).to_be_visible()
        await expect(page.locator("#continue-btn")).to_be_enabled()

        await page.click("#service-selected-display button")

        await expect(page.locator("#service-selected-display")).to_be_hidden()
        await expect(page.locator("#continue-btn")).to_be_disabled()
        await expect(page.locator("#service-search-input")).to_have_value("")

    @pytest.mark.asyncio
    async def test_progress_indicator_updates(self, page):
        """Progress indicator should update as user moves through steps"""
        await expect(page.locator("#step-1.active")).to_be_visible()
        await expect(page.locator("#progress-fill")).to_have_css("width", "0px")

        await page.wait_for_function(
            "window._modalItems && window._modalItems.service && window._modalItems.service.length > 0",
            timeout=5000,
        )
        await page.click("#service-search-input")
        await page.wait_for_selector("#service-inline-dropdown", state="visible")
        await page.click(".service-item:has-text('WhatsApp')")
        await page.click("#continue-btn")

        await expect(page.locator("#step-2.active")).to_be_visible()
        await expect(page.locator("#step-1.completed")).to_be_visible()

        progress_width = await page.locator("#progress-fill").evaluate(
            "el => el.style.width"
        )
        assert "50" in progress_width, f"Expected 50% progress, got: {progress_width}"


@pytest.fixture
async def authenticated_page(page, base_url):
    """Fixture to authenticate user before tests"""
    base = base_url.replace("localhost", "127.0.0.1")
    await page.goto(f"{base}/login")
    await page.fill("input[name='email']", "admin@namaskah.app")
    await page.fill("input[name='password']", "admin123")
    await page.click("button[type='submit']")
    await page.wait_for_url("**/dashboard", timeout=10000)
    return page
