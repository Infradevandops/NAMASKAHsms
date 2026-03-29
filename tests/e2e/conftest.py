"""E2E test configuration and fixtures."""

import os
import pytest
from playwright.async_api import async_playwright, Browser, Page


@pytest.fixture
async def browser():
    """Function-scoped browser fixture using async API."""
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        yield browser
        await browser.close()


@pytest.fixture
async def page(browser: Browser):
    """Function-scoped page fixture."""
    context = await browser.new_context()
    page = await context.new_page()
    yield page
    await page.close()
    await context.close()


@pytest.fixture(scope="session")
def base_url():
    """Base URL for E2E tests."""
    return os.getenv("BASE_URL", "http://localhost:8000")


@pytest.fixture
def test_user():
    """Test user credentials."""
    return {
        "email": os.getenv("TEST_USER_EMAIL", "admin@namaskah.app"),
        "password": os.getenv("TEST_USER_PASSWORD", "test-password-123"),
    }


@pytest.fixture
def test_timeout():
    """Test timeout in milliseconds."""
    return int(os.getenv("TEST_TIMEOUT", "30000"))
