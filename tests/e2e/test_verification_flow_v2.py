"""
E2E Tests for Modernized Verification Flow (V2)
Tests the immersive modal UI, error handling, and fallback logic.
"""

import pytest
from playwright.async_api import Page, expect


@pytest.fixture
async def authenticated_page(page: Page, base_url):
    """Fixture to authenticate user and navigate to verification page before each test"""
    base = base_url.replace("localhost", "127.0.0.1")

    # 1. Login
    await page.goto(f"{base}/login", timeout=15000)
    await page.fill("#email", "admin@namaskah.app")
    await page.fill("#password", "<admin-password>")
    await page.click("button[type='submit']")
    await page.wait_for_url("**/dashboard", timeout=15000)

    # 2. Go to verification
    await page.goto(f"{base}/verify", timeout=15000)
    await page.wait_for_load_state("networkidle")
    return page


@pytest.mark.asyncio
async def test_service_loading_error_and_retry(page: Page):
    """Test Case for Priority 0 & 1: API Failure -> Error State -> Retry -> Success"""

    # 1. Mock API to fail
    await page.route(
        "**/api/verification/services*",
        lambda route: route.fulfill(
            status=503,
            content_type="application/json",
            body='{"error": "Service unavailable"}',
        ),
    )

    await page.reload()
    await page.wait_for_load_state("networkidle")

    # 2. Verify error state
    service_input = page.locator("#service-search-input")
    await expect(service_input).to_be_disabled()
    await expect(service_input).to_have_attribute(
        "placeholder", "Services unavailable - please refresh page"
    )

    # 3. Enable API and Retry
    await page.route(
        "**/api/verification/services*",
        lambda route: route.fulfill(
            status=200,
            content_type="application/json",
            body='{"services": [{"id": "telegram", "name": "Telegram", "price": 0.50}], "total": 1}',
        ),
    )

    # Click retry button
    await page.click("#service-retry-btn")

    # Verify recovered
    await expect(service_input).to_be_enabled(timeout=15000)
    await expect(service_input).to_have_attribute(
        "placeholder", "Search services e.g. Telegram, WhatsApp...", timeout=10000
    )


@pytest.mark.asyncio
async def test_immersive_modal_opens(page: Page):
    """Test that clicking service selection opens the immersive modal"""
    # Wait for services
    await page.wait_for_function(
        "window._modalItems && window._modalItems.service && window._modalItems.service.length > 0",
        timeout=20000,
    )

    await page.click("#service-search-input")

    modal = page.locator("#immersive-modal-container")
    await expect(modal).not_to_be_empty()
    await expect(page.locator(".immersive-modal-title")).to_have_text("Select Service")


@pytest.mark.asyncio
async def test_area_code_fallback_and_receipt(page: Page):
    """Test Case for Priority 1.5: Fallback warning and receipt accuracy"""

    # 1. Setup mocks for successful service loading
    await page.route(
        "**/api/verification/services*",
        lambda route: route.fulfill(
            status=200,
            content_type="application/json",
            body='{"services": [{"id": "telegram", "name": "Telegram", "price": 1.50}], "total": 1}',
        ),
    )

    # 2. Mock purchase response WITH fallback
    await page.route(
        "**/api/verification/request",
        lambda route: route.fulfill(
            status=200,
            content_type="application/json",
            body="""{\n            "success": true,\n            "verification_id": "test_v_fallback",\n            "phone_number": "14155550199",\n            "carrier": "T-Mobile",\n            "assigned_area_code": "415",\n            "requested_area_code": "212",\n            "fallback_applied": true,\n            "same_state_fallback": false\n        }""",
        ),
    )

    # 3. Mock polling status to completed
    await page.route(
        "**/api/verification/status/*",
        lambda route: route.fulfill(
            status=200,
            content_type="application/json",
            body="""{\n            "status": "completed",\n            "sms_code": "123456",\n            "assigned_carrier": "T-Mobile",\n            "assigned_area_code": "415",\n            "fallback_applied": true,\n            "requested_area_code": "212"\n        }""",
        ),
    )

    # 4. Perform flow
    await page.click("#service-search-input")
    await page.wait_for_selector(".list-item", state="visible")
    await page.click(".list-item:has-text('Telegram')")

    await page.click("#continue-btn")
    await page.click("#get-number-btn")

    # 5. Verify Fallback Warning shown in Step 3
    warning = page.locator("#fallback-warning")
    await expect(warning).to_be_visible()
    await expect(warning).to_contain_text("212 unavailable")

    # 6. Verify Receipt Details
    await page.wait_for_selector("#code-received", state="visible", timeout=10000)

    await expect(page.locator("#receipt-carrier")).to_have_text("T-Mobile")
    await expect(page.locator("#receipt-area-code")).to_have_text("415")
    await expect(page.locator("#receipt-fallback-row")).to_be_visible()
    await expect(page.locator("#receipt-requested-ac")).to_have_text("212")


@pytest.mark.asyncio
async def test_carrier_mismatch_error(page: Page):
    """Test Case for Priority 2.3: Carrier mismatch raises 409 and shown to user"""

    # 1. Mock purchase failure with 409
    await page.route(
        "**/api/verification/request",
        lambda route: route.fulfill(
            status=409,
            content_type="application/json",
            body='{"detail": "Requested carrier Verizon was unavailable. Got T-Mobile. Verification cancelled."}',
        ),
    )

    # 2. Select service and proceed
    await page.wait_for_function(
        "window._modalItems && window._modalItems.service && window._modalItems.service.length > 0"
    )
    await page.click("#service-search-input")
    await page.click(".list-item:has-text('Telegram')")
    await page.click("#continue-btn")

    # 3. Click Get Number
    await page.click("#get-number-btn")

    # 4. Verify Error Toast or Message
    await expect(page.locator(".toast-error")).to_contain_text(
        "Requested carrier Verizon was unavailable", timeout=15000
    )
