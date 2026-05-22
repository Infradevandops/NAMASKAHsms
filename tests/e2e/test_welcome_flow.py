"""E2E tests for the 6-step onboarding wizard (OB-24 to OB-32)."""

import pytest
from playwright.async_api import Page, expect

BASE = "http://localhost:8000"


# ── OB-24: page loads ─────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_welcome_page_loads(page: Page):
    """OB-24: /welcome returns 200 and shows step 1."""
    await page.goto(f"{BASE}/welcome")
    await expect(page.locator("h1")).to_contain_text("Welcome to VRENUM SMS")
    await expect(page.locator("#language")).to_be_visible()
    await expect(page.locator("#currency")).to_be_visible()
    await expect(page.locator("#step-label")).to_contain_text("Step 1 of 6")


# ── OB-25: step 1 advances to step 2 ─────────────────────────────────────────


@pytest.mark.asyncio
async def test_step_1_advances_to_step_2(page: Page):
    """OB-25: filling step 1 and clicking Continue shows step 2."""
    await page.goto(f"{BASE}/welcome")
    await page.select_option("#language", "en")
    await page.select_option("#currency", "USD")
    await page.click("button[type='submit']")
    await expect(page.locator("#step-label")).to_contain_text("Step 2 of 6")
    await expect(page.locator("#step-2")).to_be_visible()


# ── OB-26: skip exits to dashboard ───────────────────────────────────────────


@pytest.mark.asyncio
async def test_skip_exits_to_dashboard(page: Page):
    """OB-26: clicking Skip on any step redirects to /dashboard."""
    await page.goto(f"{BASE}/welcome")
    await page.click("text=Skip →")
    # Unauthenticated users get redirected to /login by dashboard auth guard
    assert "/dashboard" in page.url or "/login" in page.url


# ── OB-27: back button works ──────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_back_button_works(page: Page):
    """OB-27: advancing to step 3 then clicking Back shows step 2."""
    await page.goto(f"{BASE}/welcome")
    await page.select_option("#language", "en")
    await page.select_option("#currency", "USD")
    await page.click("button[type='submit']")  # → step 2
    await page.click("text=Next →")  # → step 3
    await expect(page.locator("#step-label")).to_contain_text("Step 3 of 6")
    await page.click("text=← Back")
    await expect(page.locator("#step-label")).to_contain_text("Step 2 of 6")
    await expect(page.locator("#step-2")).to_be_visible()


# ── OB-28: complete all steps ─────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_complete_all_steps_redirects_dashboard(page: Page):
    """OB-28: advancing through all 6 steps lands on /dashboard or /login."""
    await page.goto(f"{BASE}/welcome")
    await page.select_option("#language", "en")
    await page.select_option("#currency", "USD")
    await page.click("button[type='submit']")  # step 1 → 2
    for _ in range(3):  # steps 2 → 3 → 4 → 5
        await page.click("text=Next →")
    await page.click("text=Next →")  # step 5 → 6
    await page.click("text=Go to Dashboard 🚀")
    assert "/dashboard" in page.url or "/login" in page.url


# ── OB-29 & OB-30: tier-aware steps ──────────────────────────────────────────


@pytest.mark.asyncio
async def test_freemium_sees_upgrade_cta_on_step_5(page: Page):
    """OB-30: unauthenticated/freemium user sees upgrade CTA on step 5."""
    await page.goto(f"{BASE}/welcome")
    await page.select_option("#language", "en")
    await page.select_option("#currency", "USD")
    await page.click("button[type='submit']")
    for _ in range(3):
        await page.click("text=Next →")
    # Now on step 5
    await expect(page.locator("#step-label")).to_contain_text("Step 5 of 6")
    await expect(page.locator("#step5-upgrade")).to_be_visible()
    await expect(page.locator("#step5-pro")).to_be_hidden()


# ── OB-31: mobile responsive ─────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_mobile_responsive(page: Page):
    """OB-31: wizard renders correctly at 375px."""
    await page.set_viewport_size({"width": 375, "height": 667})
    await page.goto(f"{BASE}/welcome")
    await expect(page.locator("h1")).to_be_visible()
    await expect(page.locator("#language")).to_be_visible()
    await expect(page.locator("#step-label")).to_be_visible()


# ── OB-32: progress bar updates ──────────────────────────────────────────────


@pytest.mark.asyncio
async def test_progress_bar_updates(page: Page):
    """OB-32: step label updates correctly as user advances."""
    await page.goto(f"{BASE}/welcome")
    await expect(page.locator("#step-label")).to_contain_text("Step 1 of 6")

    await page.select_option("#language", "en")
    await page.select_option("#currency", "USD")
    await page.click("button[type='submit']")
    await expect(page.locator("#step-label")).to_contain_text("Step 2 of 6")

    await page.click("text=Next →")
    await expect(page.locator("#step-label")).to_contain_text("Step 3 of 6")


# ── Existing preference tests (kept) ─────────────────────────────────────────


@pytest.mark.asyncio
async def test_language_selection(page: Page):
    await page.goto(f"{BASE}/welcome")
    await page.select_option("#language", "en")
    assert await page.locator("#language").input_value() == "en"


@pytest.mark.asyncio
async def test_currency_selection(page: Page):
    await page.goto(f"{BASE}/welcome")
    await page.select_option("#currency", "USD")
    assert await page.locator("#currency").input_value() == "USD"


@pytest.mark.asyncio
async def test_form_validation(page: Page):
    """Step 1 form requires both selections before advancing."""
    await page.goto(f"{BASE}/welcome")
    await page.click("button[type='submit']")
    await expect(page.locator("#step-label")).to_contain_text("Step 1 of 6")


@pytest.mark.asyncio
async def test_preferences_persist(page: Page):
    """Preferences saved to localStorage persist on reload."""
    await page.goto(f"{BASE}/welcome")
    await page.select_option("#language", "es")
    await page.select_option("#currency", "EUR")
    await page.click("button[type='submit']")

    await page.goto(f"{BASE}/welcome")
    assert await page.locator("#language").input_value() == "es"
    assert await page.locator("#currency").input_value() == "EUR"


@pytest.mark.asyncio
async def test_all_languages_available(page: Page):
    await page.goto(f"{BASE}/welcome")
    options = await page.locator("#language option").all_text_contents()
    assert len(options) == 11
    assert any("English" in opt for opt in options)
    assert any("Español" in opt for opt in options)


@pytest.mark.asyncio
async def test_all_currencies_available(page: Page):
    await page.goto(f"{BASE}/welcome")
    options = await page.locator("#currency option").all_text_contents()
    assert len(options) == 11
    assert any("USD" in opt for opt in options)
    assert any("EUR" in opt for opt in options)
