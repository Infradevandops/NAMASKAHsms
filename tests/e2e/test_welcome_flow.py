"""E2E test for welcome modal user flow"""

import pytest
from playwright.async_api import Page, expect


@pytest.mark.asyncio
async def test_welcome_page_loads(page: Page):
    """Test welcome page loads correctly"""
    await page.goto("http://localhost:8000/welcome")
    await expect(page.locator("h1")).to_contain_text("Welcome to Namaskah")
    await expect(page.locator("#language")).to_be_visible()
    await expect(page.locator("#currency")).to_be_visible()


@pytest.mark.asyncio
async def test_language_selection(page: Page):
    """Test language dropdown selection"""
    await page.goto("http://localhost:8000/welcome")
    await page.select_option("#language", "en")
    assert await page.locator("#language").input_value() == "en"


@pytest.mark.asyncio
async def test_currency_selection(page: Page):
    """Test currency dropdown selection"""
    await page.goto("http://localhost:8000/welcome")
    await page.select_option("#currency", "USD")
    assert await page.locator("#currency").input_value() == "USD"


@pytest.mark.asyncio
async def test_form_validation(page: Page):
    """Test form requires both selections"""
    await page.goto("http://localhost:8000/welcome")
    await page.click("button[type='submit']")
    assert page.url.endswith("/welcome")


@pytest.mark.asyncio
async def test_complete_flow(page: Page):
    """Test complete user flow from welcome to dashboard"""
    await page.goto("http://localhost:8000/welcome")
    await page.select_option("#language", "en")
    await page.select_option("#currency", "USD")
    await page.click("button[type='submit']")
    await page.wait_for_url("http://localhost:8000/")

    lang = await page.evaluate("localStorage.getItem('language')")
    curr = await page.evaluate("localStorage.getItem('currency')")
    assert lang == "en"
    assert curr == "USD"


@pytest.mark.asyncio
async def test_skip_link(page: Page):
    """Test skip functionality"""
    await page.goto("http://localhost:8000/welcome")
    await page.click("text=Skip")
    await page.wait_for_url("http://localhost:8000/")


@pytest.mark.asyncio
async def test_preferences_persist(page: Page):
    """Test preferences persist on reload"""
    await page.goto("http://localhost:8000/welcome")
    await page.select_option("#language", "es")
    await page.select_option("#currency", "EUR")
    await page.click("button[type='submit']")
    await page.wait_for_url("http://localhost:8000/")

    await page.goto("http://localhost:8000/welcome")
    assert await page.locator("#language").input_value() == "es"
    assert await page.locator("#currency").input_value() == "EUR"


@pytest.mark.asyncio
async def test_all_languages_available(page: Page):
    """Test all 10 languages are in dropdown"""
    await page.goto("http://localhost:8000/welcome")
    options = await page.locator("#language option").all_text_contents()
    assert len(options) == 11
    assert any("English" in opt for opt in options)
    assert any("Español" in opt for opt in options)


@pytest.mark.asyncio
async def test_all_currencies_available(page: Page):
    """Test all 10 currencies are in dropdown"""
    await page.goto("http://localhost:8000/welcome")
    options = await page.locator("#currency option").all_text_contents()
    assert len(options) == 11
    assert any("USD" in opt for opt in options)
    assert any("EUR" in opt for opt in options)


@pytest.mark.asyncio
async def test_mobile_responsive(page: Page):
    """Test mobile viewport"""
    await page.set_viewport_size({"width": 375, "height": 667})
    await page.goto("http://localhost:8000/welcome")
    await expect(page.locator("h1")).to_be_visible()
    await expect(page.locator("#language")).to_be_visible()
