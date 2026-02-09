"""Pytest configuration for E2E tests"""
import pytest
from playwright.sync_api import sync_playwright

@pytest.fixture(scope="session")
def browser():
    """Create browser instance for all tests"""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        yield browser
        browser.close()

@pytest.fixture
def page(browser):
    """Create new page for each test"""
    context = browser.new_context()
    page = context.new_page()
    yield page
    page.close()
    context.close()
