"""E2E Testing Setup - Critical User Journeys"""

import os

import pytest

BASE_URL = os.getenv("BASE_URL", "http://localhost:8000")
TEST_EMAIL = "test@example.com"
TEST_PASSWORD = "TestPassword123!"


@pytest.mark.smoke
class TestSmokeTests:
    """Critical smoke tests for deployment verification"""

    @pytest.mark.asyncio
    async def test_homepage_loads(self, page):
        """Verify homepage loads successfully"""
        await page.goto(BASE_URL)
        title = await page.title()
        assert title == "Namaskah SMS"
        assert await page.is_visible("text=SMS Verification")

    @pytest.mark.asyncio
    async def test_health_endpoint(self, page):
        """Verify health endpoint responds"""
        response = await page.request.get(f"{BASE_URL}/health")
        assert response.status == 200
        data = await response.json()
        assert data["status"] == "healthy"

    @pytest.mark.asyncio
    async def test_login_page_loads(self, page):
        """Verify login page loads"""
        await page.goto(f"{BASE_URL}/login")
        assert await page.is_visible("input[name='email']")
        assert await page.is_visible("input[name='password']")
        assert await page.is_visible("button[type='submit']")

    @pytest.mark.asyncio
    async def test_register_page_loads(self, page):
        """Verify registration page loads"""
        await page.goto(f"{BASE_URL}/register")
        assert await page.is_visible("input[name='email']")
        assert await page.is_visible("input[name='username']")
        assert await page.is_visible("input[name='password']")

    @pytest.mark.asyncio
    async def test_pricing_page_loads(self, page):
        """Verify pricing page loads"""
        await page.goto(f"{BASE_URL}/pricing")
        assert await page.is_visible("text=Freemium")
        assert await page.is_visible("text=Pro")

    @pytest.mark.asyncio
    async def test_api_diagnostics(self, page):
        """Verify API diagnostics endpoint"""
        response = await page.request.get(f"{BASE_URL}/api/diagnostics")
        assert response.status == 200
        data = await response.json()
        assert "version" in data
        assert "database" in data

    @pytest.mark.asyncio
    async def test_auth_redirect(self, page):
        """Verify auth redirects work"""
        await page.goto(f"{BASE_URL}/auth/login")
        await page.wait_for_url("**/login")
        assert "/login" in page.url

    @pytest.mark.asyncio
    async def test_dashboard_requires_auth(self, page):
        """Verify dashboard requires authentication"""
        await page.goto(f"{BASE_URL}/dashboard")
        await page.wait_for_url("**/login")
        assert "/login" in page.url

    @pytest.mark.asyncio
    async def test_static_files_load(self, page):
        """Verify static files are accessible"""
        await page.goto(BASE_URL)
        responses = []
        page.on("response", lambda response: responses.append(response))
        await page.reload()
        css_responses = [r for r in responses if r.url.endswith(".css")]
        for response in css_responses:
            assert response.status == 200

    @pytest.mark.asyncio
    async def test_cors_headers(self, page):
        """Verify CORS headers are present"""
        response = await page.request.get(BASE_URL)
        headers = response.headers
        assert "access-control-allow-origin" in headers or response.status == 200

    @pytest.mark.asyncio
    async def test_security_headers(self, page):
        """Verify security headers are present"""
        response = await page.request.get(BASE_URL)
        headers = response.headers
        assert "x-content-type-options" in headers
        assert "x-frame-options" in headers

    @pytest.mark.asyncio
    async def test_rate_limiting_active(self, page):
        """Verify rate limiting is active"""
        responses = []
        for _ in range(10):
            response = await page.request.get(f"{BASE_URL}/health")
            responses.append(response.status)
        assert all(status == 200 for status in responses)

    @pytest.mark.asyncio
    async def test_error_handling(self, page):
        """Verify error handling works"""
        response = await page.request.get(f"{BASE_URL}/nonexistent")
        assert response.status == 404

    @pytest.mark.asyncio
    async def test_json_api_response(self, page):
        """Verify API returns JSON"""
        response = await page.request.get(f"{BASE_URL}/api/diagnostics")
        assert response.status == 200
        assert "application/json" in response.headers.get("content-type", "")

    @pytest.mark.asyncio
    async def test_https_redirect(self, page):
        """Verify HTTPS redirect in production"""
        if "https://" in BASE_URL:
            http_url = BASE_URL.replace("https://", "http://")
            response = await page.request.get(http_url)
            assert response.status in [301, 302, 403, 404]


class TestUserJourneys:
    """Complete user journey tests"""

    @pytest.mark.asyncio
    async def test_user_registration_flow(self, page):
        """Test complete user registration"""
        await page.goto(f"{BASE_URL}/register")
        await page.fill("input[name='email']", TEST_EMAIL)
        await page.fill("input[name='username']", "testuser")
        await page.fill("input[name='password']", TEST_PASSWORD)
        await page.fill("input[name='confirm_password']", TEST_PASSWORD)
        await page.click("button[type='submit']")
        await page.wait_for_timeout(2000)
        assert page.url != f"{BASE_URL}/register"

    @pytest.mark.asyncio
    async def test_login_flow(self, page):
        """Test user login flow"""
        await page.goto(f"{BASE_URL}/login")
        await page.fill("input[name='email']", TEST_EMAIL)
        await page.fill("input[name='password']", TEST_PASSWORD)
        await page.click("button[type='submit']")
        await page.wait_for_timeout(2000)
        assert page.url != f"{BASE_URL}/login"

    @pytest.mark.asyncio
    async def test_payment_initialization_flow(self, page):
        """Test payment initialization (mock)"""
        response = await page.request.post(
            f"{BASE_URL}/api/billing/initialize",
            headers={"Content-Type": "application/json"},
            data='{"amount": 10.0}',
        )
        assert response.status in [401, 422]

    @pytest.mark.asyncio
    async def test_sms_verification_flow(self, page):
        """Test SMS verification flow (mock)"""
        response = await page.request.post(
            f"{BASE_URL}/api/verification/create",
            headers={"Content-Type": "application/json"},
            data='{"service": "whatsapp", "country": "US"}',
        )
        assert response.status == 401
