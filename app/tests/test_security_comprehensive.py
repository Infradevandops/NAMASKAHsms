"""Comprehensive security test suite."""
import pytest
from fastapi.testclient import TestClient
from app.main import app


class TestSecurityComprehensive:
    """Comprehensive security tests covering all major vulnerabilities."""

    @pytest.fixture
    def client(self):
        """Test client fixture."""
        return TestClient(app)

    def test_sql_injection_protection(self, client):
        """Test SQL injection protection in API endpoints."""
        sql_payloads = [
            "'; DROP TABLE users; --",
            "' OR '1'='1",
            "1; DELETE FROM verifications; --",
            "admin'--",
            "' UNION SELECT * FROM users --"
        ]

        for payload in sql_payloads:
            # Test in query parameters
            response = client.get(f"/api/verify/history?search={payload}")
            assert response.status_code in [200, 401, 422]  # Should not cause 500 error

            # Test in path parameters
            response = client.get(f"/api/verify/{payload}")
            assert response.status_code in [404, 401, 422]  # Should not cause 500 error

    def test_xss_protection(self, client):
        """Test XSS protection in API responses."""
        xss_payloads = [
            "<script>alert('xss')</script>",
            "javascript:alert('xss')",
            "<img src = x onerror = alert('xss')>",
            "<svg onload = alert('xss')>",
            "';alert('xss');//"
        ]

        for payload in xss_payloads:
            # Test that payload is sanitized
            sanitized = sanitize_html(payload)
            assert "<script>" not in sanitized
            assert "javascript:" not in sanitized
            assert "onerror=" not in sanitized
            assert "onload=" not in sanitized

    def test_log_injection_protection(self):
        """Test log injection protection."""
        log_payloads = [
            "Normal input\nFAKE: Admin login successful",
            "Input\r\nERROR: System compromised",
            "Data\x1b[2J\x1b[HScreen clear attack",
            "Text\x00NULL byte injection"
        ]

        for payload in log_payloads:
            sanitized = sanitize_log_input(payload)
            assert "\n" not in sanitized
            assert "\r" not in sanitized
            assert "\x1b" not in sanitized
            assert "\x00" not in sanitized

    def test_authentication_required(self, client):
        """Test that protected endpoints require authentication."""
        protected_endpoints = [
            "/api/verify/create",
            "/api/verify/history",
            "/admin/users",
            "/admin/stats"
        ]

        for endpoint in protected_endpoints:
            response = client.post(endpoint)
            assert response.status_code == 401

    def test_admin_authorization(self, client):
        """Test that admin endpoints require admin role."""
        admin_endpoints = [
            "/admin/users",
            "/admin/stats",
            "/admin/support/tickets"
        ]

        # Test without authentication
        for endpoint in admin_endpoints:
            response = client.get(endpoint)
            assert response.status_code in [401, 403]

    def test_input_validation(self, client):
        """Test input validation on API endpoints."""
        # Test invalid email formats
        invalid_emails = [
            "invalid - email",
            "@invalid.com",
            "test@",
            "test..test@example.com"
        ]

        for email in invalid_emails:
            response = client.post("/auth/register", json={
                "email": email,
                "password": "validpassword123"
            })
            assert response.status_code == 422

    def test_rate_limiting_headers(self, client):
        """Test that rate limiting headers are present."""
        response = client.get("/")
        # Should have security headers
        assert "X - Content-Type - Options" in response.headers
        assert "X - Frame-Options" in response.headers
        assert "Content - Security-Policy" in response.headers

    def test_sensitive_data_exposure(self, client):
        """Test that sensitive data is not exposed in responses."""
        # Test health endpoint doesn't expose sensitive info
        response = client.get("/health")
        if response.status_code == 200:
            data = response.json()
            # Should not contain sensitive database info
            assert "password" not in str(data).lower()
            assert "secret" not in str(data).lower()
            assert "api_key" not in str(data).lower()

    def test_cors_headers(self, client):
        """Test CORS headers are properly configured."""
        response = client.options("/", headers={"Origin": "https://example.com"})
        # Should have proper CORS headers
        assert "Access - Control-Allow - Methods" in response.headers

    def test_content_type_validation(self, client):
        """Test content type validation."""
        # Test with invalid content type
        response = client.post(
            "/auth/login",
            data="invalid data",
            headers={"Content - Type": "text/plain"}
        )
        assert response.status_code == 422

    def test_file_upload_security(self, client):
        """Test file upload security (if applicable)."""
        # Test malicious file extensions
        malicious_files = [
            ("test.php", b"<?php echo 'test'; ?>"),
            ("test.exe", b"MZ\x90\x00"),
            ("test.js", b"alert('xss');")
        ]

        for filename, content in malicious_files:
            # If file upload endpoint exists, test it
            # This is a placeholder - adjust based on actual endpoints
            pass

    def test_parameter_pollution(self, client):
        """Test HTTP parameter pollution protection."""
        # Test duplicate parameters
        response = client.get("/api/verify/history?limit = 10&limit = 1000")
        assert response.status_code in [200, 401, 422]

    def test_method_override_protection(self, client):
        """Test HTTP method override protection."""
        # Test X - HTTP-Method - Override header
        response = client.post(
            "/api/verify/history",
            headers={"X - HTTP-Method - Override": "DELETE"}
        )
        # Should not allow method override for security
        assert response.status_code in [401, 405, 422]

    def test_host_header_injection(self, client):
        """Test Host header injection protection."""
        malicious_hosts = [
            "evil.com",
            "localhost:8000\r\nX - Injected: header",
            "example.com\nSet - Cookie: evil = true"
        ]

        for host in malicious_hosts:
            response = client.get("/", headers={"Host": host})
            # Should handle malicious hosts gracefully
            assert response.status_code != 500

    def test_user_enumeration_protection(self, client):
        """Test protection against user enumeration."""
        # Test login with non - existent user
        response1 = client.post("/auth/login", json={
            "email": "nonexistent@example.com",
            "password": "password123"
        })

        # Test login with existing user but wrong password
        response2 = client.post("/auth/login", json={
            "email": "test@example.com",
            "password": "wrongpassword"
        })

        # Responses should be similar to prevent user enumeration
        assert response1.status_code == response2.status_code

    def test_timing_attack_protection(self, client):
        """Test protection against timing attacks."""
        import time

        # Test password verification timing
        start_time = time.time()
        client.post("/auth/login", json={
            "email": "test@example.com",
            "password": "short"
        })
        short_time = time.time() - start_time

        start_time = time.time()
        client.post("/auth/login", json={
            "email": "test@example.com",
            "password": "verylongpasswordthatshouldbeconstanttime"
        })
        long_time = time.time() - start_time

        # Time difference should be minimal (within 100ms)
        assert abs(short_time - long_time) < 0.1

    def test_session_security(self, client):
        """Test session security measures."""
        # Test that sessions expire properly
        # Test that session tokens are secure
        # This would need actual session implementation

    def test_csrf_protection(self, client):
        """Test CSRF protection (if implemented)."""
        # Test that state - changing operations require CSRF tokens
        # This would depend on CSRF implementation

    def test_clickjacking_protection(self, client):
        """Test clickjacking protection."""
        response = client.get("/")
        # Should have X - Frame-Options header
        assert response.headers.get("X - Frame-Options") == "DENY"

    def test_mime_sniffing_protection(self, client):
        """Test MIME sniffing protection."""
        response = client.get("/")
        # Should have X - Content-Type - Options header
        assert response.headers.get("X - Content-Type - Options") == "nosnif"

    def test_information_disclosure(self, client):
        """Test for information disclosure vulnerabilities."""
        # Test error responses don't leak sensitive info
        response = client.get("/nonexistent - endpoint")
        assert response.status_code == 404

        if response.status_code >= 400:
            error_text = response.text.lower()
            # Should not contain sensitive paths or stack traces
            assert "/users/" not in error_text
            assert "traceback" not in error_text
            assert "exception" not in error_text

    def test_security_headers_comprehensive(self, client):
        """Test comprehensive security headers."""
        response = client.get("/")

        required_headers = [
            "X - Content-Type - Options",
            "X - Frame-Options",
            "Content - Security-Policy",
            "X - XSS-Protection",
            "Referrer - Policy"
        ]

        for header in required_headers:
            assert header in response.headers, f"Missing security header: {header}"
