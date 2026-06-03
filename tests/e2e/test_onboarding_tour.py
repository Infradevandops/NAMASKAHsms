"""
Onboarding Tour - Automated Stability Tests
Tests driver.js integration and tour functionality
"""

import time

import pytest
from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait


class TestOnboardingTour:
    """Test suite for driver.js onboarding tour"""

    @pytest.fixture
    def browser(self):
        """Setup Chrome browser in headless mode"""
        options = webdriver.ChromeOptions()
        options.add_argument("--headless")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        driver = webdriver.Chrome(options=options)
        driver.set_window_size(1920, 1080)
        yield driver
        driver.quit()

    @pytest.fixture
    def authenticated_session(self, browser):
        """Create test user and authenticate"""
        # Navigate to register page
        browser.get("http://localhost:8000/register")

        # Fill registration form
        email_input = browser.find_element(By.ID, "email")
        password_input = browser.find_element(By.ID, "password")
        terms_checkbox = browser.find_element(By.ID, "terms_accepted")

        test_email = f"test_tour_{int(time.time())}@example.com"
        email_input.send_keys(test_email)
        password_input.send_keys("TestPassword123!")
        terms_checkbox.click()

        # Submit form
        submit_btn = browser.find_element(By.CSS_SELECTOR, "button[type='submit']")
        submit_btn.click()

        # Wait for redirect to dashboard
        WebDriverWait(browser, 10).until(EC.url_contains("/dashboard"))

        return browser

    def test_tour_auto_starts_on_dashboard(self, authenticated_session):
        """Test: Tour automatically starts for new users"""
        browser = authenticated_session

        # Wait for tour to initialize (1.5s delay + some buffer)
        time.sleep(2)

        # Check if driver.js popover exists
        try:
            popover = WebDriverWait(browser, 5).until(
                EC.presence_of_element_located((By.CLASS_NAME, "driver-popover"))
            )
            assert popover.is_displayed(), "Tour popover should be visible"
            print("✓ Tour auto-started successfully")
        except TimeoutException:
            pytest.fail("Tour did not start within 5 seconds")

    def test_tour_shows_welcome_step(self, authenticated_session):
        """Test: First step shows welcome message"""
        browser = authenticated_session
        time.sleep(2)

        try:
            title = WebDriverWait(browser, 5).until(
                EC.presence_of_element_located((By.CLASS_NAME, "driver-popover-title"))
            )
            assert "Welcome" in title.text, "First step should show welcome message"
            print(f"✓ Welcome message displayed: {title.text}")
        except TimeoutException:
            pytest.fail("Welcome step not found")

    def test_tour_navigation_next_button(self, authenticated_session):
        """Test: Next button advances through steps"""
        browser = authenticated_session
        time.sleep(2)

        try:
            # Click next button
            next_btn = WebDriverWait(browser, 5).until(
                EC.element_to_be_clickable((By.CLASS_NAME, "driver-popover-next-btn"))
            )
            next_btn.click()

            time.sleep(0.5)

            # Verify step changed
            title = browser.find_element(By.CLASS_NAME, "driver-popover-title")
            assert "Currency" in title.text, "Second step should be about currency"
            print(f"✓ Navigation worked: {title.text}")
        except TimeoutException:
            pytest.fail("Next button not found or not clickable")

    def test_tour_navigation_previous_button(self, authenticated_session):
        """Test: Previous button goes back"""
        browser = authenticated_session
        time.sleep(2)

        try:
            # Go to step 2
            next_btn = WebDriverWait(browser, 5).until(
                EC.element_to_be_clickable((By.CLASS_NAME, "driver-popover-next-btn"))
            )
            next_btn.click()
            time.sleep(0.5)

            # Go back to step 1
            prev_btn = browser.find_element(By.CLASS_NAME, "driver-popover-prev-btn")
            prev_btn.click()
            time.sleep(0.5)

            # Verify back at step 1
            title = browser.find_element(By.CLASS_NAME, "driver-popover-title")
            assert "Welcome" in title.text, "Should be back at welcome step"
            print("✓ Previous button works")
        except Exception as e:
            pytest.fail(f"Previous button test failed: {str(e)}")

    def test_tour_skip_button(self, authenticated_session):
        """Test: Skip button closes tour and marks complete"""
        browser = authenticated_session
        time.sleep(2)

        try:
            # Click skip button
            skip_btn = WebDriverWait(browser, 5).until(
                EC.element_to_be_clickable((By.CLASS_NAME, "driver-popover-close-btn"))
            )
            skip_btn.click()

            time.sleep(0.5)

            # Verify tour closed
            popovers = browser.find_elements(By.CLASS_NAME, "driver-popover")
            assert len(popovers) == 0, "Tour should be closed after skip"

            # Verify localStorage flag
            completed = browser.execute_script(
                "return localStorage.getItem('onboarding_tour_completed')"
            )
            assert completed == "true", "Tour completion should be cached"
            print("✓ Skip button works and marks completion")
        except Exception as e:
            pytest.fail(f"Skip button test failed: {str(e)}")

    def test_tour_completion_flow(self, authenticated_session):
        """Test: Complete all steps and verify completion"""
        browser = authenticated_session
        time.sleep(2)

        try:
            # Count steps and click through all
            steps_count = 0
            while True:
                try:
                    next_btn = browser.find_element(
                        By.CLASS_NAME, "driver-popover-next-btn"
                    )
                    next_btn.click()
                    steps_count += 1
                    time.sleep(0.3)
                except:
                    # No more next button, try done button
                    try:
                        done_btn = browser.find_element(
                            By.CLASS_NAME, "driver-popover-next-btn"
                        )
                        done_btn.click()
                        break
                    except:
                        break

            time.sleep(1)

            # Verify tour closed
            popovers = browser.find_elements(By.CLASS_NAME, "driver-popover")
            assert len(popovers) == 0, "Tour should close after completion"

            print(f"✓ Completed tour with {steps_count} steps")
        except Exception as e:
            pytest.fail(f"Tour completion test failed: {str(e)}")

    def test_tour_does_not_restart_after_completion(self, authenticated_session):
        """Test: Tour doesn't show again after completion"""
        browser = authenticated_session
        time.sleep(2)

        # Complete tour
        try:
            skip_btn = WebDriverWait(browser, 5).until(
                EC.element_to_be_clickable((By.CLASS_NAME, "driver-popover-close-btn"))
            )
            skip_btn.click()
            time.sleep(1)

            # Refresh page
            browser.refresh()
            time.sleep(3)

            # Verify tour doesn't start again
            popovers = browser.find_elements(By.CLASS_NAME, "driver-popover")
            assert len(popovers) == 0, "Tour should not restart after completion"
            print("✓ Tour does not restart after completion")
        except Exception as e:
            pytest.fail(f"Restart prevention test failed: {str(e)}")

    def test_tour_arrows_point_to_elements(self, authenticated_session):
        """Test: Verify arrows are rendered correctly"""
        browser = authenticated_session
        time.sleep(2)

        try:
            # Advance to currency step (has arrow)
            next_btn = WebDriverWait(browser, 5).until(
                EC.element_to_be_clickable((By.CLASS_NAME, "driver-popover-next-btn"))
            )
            next_btn.click()
            time.sleep(0.5)

            # Check for arrow element
            arrows = browser.find_elements(By.CLASS_NAME, "driver-popover-arrow")
            assert len(arrows) > 0, "Arrow should be present"
            print("✓ Arrows render correctly")
        except Exception as e:
            pytest.fail(f"Arrow rendering test failed: {str(e)}")

    def test_tour_mobile_responsive(self, authenticated_session):
        """Test: Tour works on mobile screen size"""
        browser = authenticated_session

        # Resize to mobile
        browser.set_window_size(375, 667)
        time.sleep(2)

        try:
            popover = WebDriverWait(browser, 5).until(
                EC.presence_of_element_located((By.CLASS_NAME, "driver-popover"))
            )

            # Check popover is within viewport
            popover_width = popover.size["width"]
            viewport_width = browser.execute_script("return window.innerWidth")

            assert (
                popover_width <= viewport_width
            ), "Popover should fit in mobile viewport"
            print("✓ Mobile responsive works")
        except Exception as e:
            pytest.fail(f"Mobile responsive test failed: {str(e)}")

    def test_driver_js_loaded(self, authenticated_session):
        """Test: Verify driver.js library loaded"""
        browser = authenticated_session

        driver_loaded = browser.execute_script(
            "return typeof window.driver !== 'undefined'"
        )
        assert driver_loaded, "driver.js should be loaded"
        print("✓ driver.js library loaded")

    def test_tour_module_loaded(self, authenticated_session):
        """Test: Verify onboarding tour module loaded"""
        browser = authenticated_session

        tour_loaded = browser.execute_script(
            "return typeof window.onboardingTour !== 'undefined'"
        )
        assert tour_loaded, "onboardingTour module should be loaded"
        print("✓ onboardingTour module loaded")

    def test_backend_completion_endpoint(self, authenticated_session):
        """Test: Verify backend marks completion correctly"""
        browser = authenticated_session
        time.sleep(2)

        # Complete tour
        try:
            skip_btn = WebDriverWait(browser, 5).until(
                EC.element_to_be_clickable((By.CLASS_NAME, "driver-popover-close-btn"))
            )
            skip_btn.click()
            time.sleep(2)  # Wait for backend call

            # Check backend status
            token = browser.execute_script(
                "return localStorage.getItem('access_token')"
            )

            # Make API call via browser
            completed = browser.execute_script(
                f"""
                return fetch('/api/auth/onboarding-status', {{
                    headers: {{ 'Authorization': 'Bearer {token}' }}
                }})
                .then(r => r.json())
                .then(d => d.completed)
                .catch(() => false);
            """
            )

            time.sleep(1)
            assert completed, "Backend should mark onboarding as completed"
            print("✓ Backend completion endpoint works")
        except Exception as e:
            pytest.fail(f"Backend completion test failed: {str(e)}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
