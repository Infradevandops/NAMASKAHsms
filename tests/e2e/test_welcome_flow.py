"""E2E test for welcome modal user flow"""


from playwright.sync_api import Page, expect

def test_welcome_page_loads(page: Page):

    """Test welcome page loads correctly"""
    page.goto("http://localhost:8000/welcome")
    expect(page.locator("h1")).to_contain_text("Welcome to Namaskah")
    expect(page.locator("#language")).to_be_visible()
    expect(page.locator("#currency")).to_be_visible()


def test_language_selection(page: Page):

    """Test language dropdown selection"""
    page.goto("http://localhost:8000/welcome")
    page.select_option("#language", "en")
    assert page.locator("#language").input_value() == "en"


def test_currency_selection(page: Page):

    """Test currency dropdown selection"""
    page.goto("http://localhost:8000/welcome")
    page.select_option("#currency", "USD")
    assert page.locator("#currency").input_value() == "USD"


def test_form_validation(page: Page):

    """Test form requires both selections"""
    page.goto("http://localhost:8000/welcome")
    page.click("button[type='submit']")
    assert page.url.endswith("/welcome")


def test_complete_flow(page: Page):

    """Test complete user flow from welcome to dashboard"""
    page.goto("http://localhost:8000/welcome")
    page.select_option("#language", "en")
    page.select_option("#currency", "USD")
    page.click("button[type='submit']")
    page.wait_for_url("http://localhost:8000/")

    lang = page.evaluate("localStorage.getItem('language')")
    curr = page.evaluate("localStorage.getItem('currency')")
    assert lang == "en"
    assert curr == "USD"


def test_skip_link(page: Page):

    """Test skip functionality"""
    page.goto("http://localhost:8000/welcome")
    page.click("text=Skip")
    page.wait_for_url("http://localhost:8000/")


def test_preferences_persist(page: Page):

    """Test preferences persist on reload"""
    page.goto("http://localhost:8000/welcome")
    page.select_option("#language", "es")
    page.select_option("#currency", "EUR")
    page.click("button[type='submit']")
    page.wait_for_url("http://localhost:8000/")

    page.goto("http://localhost:8000/welcome")
    assert page.locator("#language").input_value() == "es"
    assert page.locator("#currency").input_value() == "EUR"


def test_all_languages_available(page: Page):

    """Test all 10 languages are in dropdown"""
    page.goto("http://localhost:8000/welcome")
    options = page.locator("#language option").all_text_contents()
    assert len(options) == 11
    assert any("English" in opt for opt in options)
    assert any("Español" in opt for opt in options)


def test_all_currencies_available(page: Page):

    """Test all 10 currencies are in dropdown"""
    page.goto("http://localhost:8000/welcome")
    options = page.locator("#currency option").all_text_contents()
    assert len(options) == 11
    assert any("USD" in opt for opt in options)
    assert any("EUR" in opt for opt in options)


def test_mobile_responsive(page: Page):

    """Test mobile viewport"""
    page.set_viewport_size({"width": 375, "height": 667})
    page.goto("http://localhost:8000/welcome")
    expect(page.locator("h1")).to_be_visible()
    expect(page.locator("#language")).to_be_visible()