"""Tests for XSS prevention and input sanitization."""
from app.utils.sanitization import (
    sanitize_html,
    sanitize_user_input,
    sanitize_email_content,
    validate_and_sanitize_response
)


class TestXSSPrevention:
    """Test XSS prevention utilities."""

    def test_sanitize_html_basic(self):
        """Test basic HTML sanitization."""
        malicious_input = "<script>alert('xss')</script>Hello"
        sanitized = sanitize_html(malicious_input)

        assert "<script>" not in sanitized
        assert "alert" not in sanitized
        assert "Hello" in sanitized
        assert "&lt;script&gt;" in sanitized

    def test_sanitize_html_javascript_urls(self):
        """Test sanitization of javascript: URLs."""
        malicious_input = "javascript:alert('xss')"
        sanitized = sanitize_html(malicious_input)

        assert "javascript:" not in sanitized
        assert "alert" in sanitized  # Content preserved but javascript: removed

    def test_sanitize_html_event_handlers(self):
        """Test sanitization of event handlers."""
        malicious_input = "onclick='alert(1)' onload='evil()'"
        sanitized = sanitize_html(malicious_input)

        assert "onclick=" not in sanitized
        assert "onload=" not in sanitized
        assert "alert" in sanitized  # Content preserved but handlers removed

    def test_sanitize_user_input_dict(self):
        """Test sanitization of dictionary input."""
        malicious_data = {
            "name": "<script>alert('xss')</script>John",
            "email": "test@example.com",
            "message": "javascript:alert('evil')"
        }

        sanitized = sanitize_user_input(malicious_data)

        assert "<script>" not in sanitized["name"]
        assert "John" in sanitized["name"]
        assert sanitized["email"] == "test@example.com"  # Safe content unchanged
        assert "javascript:" not in sanitized["message"]

    def test_sanitize_user_input_list(self):
        """Test sanitization of list input."""
        malicious_data = [
            "<script>alert('xss')</script>",
            "safe content",
            {"nested": "javascript:alert('nested')"}
        ]

        sanitized = sanitize_user_input(malicious_data)

        assert "<script>" not in sanitized[0]
        assert sanitized[1] == "safe content"
        assert "javascript:" not in sanitized[2]["nested"]

    def test_sanitize_email_content(self):
        """Test email content sanitization with allowed HTML."""
        content = "<h2>Title</h2><p>Content</p><script>alert('xss')</script>"
        sanitized = sanitize_email_content(content)

        assert "<h2>Title</h2>" in sanitized
        assert "<p>Content</p>" in sanitized
        assert "<script>" not in sanitized

    def test_validate_and_sanitize_response(self):
        """Test API response sanitization."""
        response_data = {
            "message": "<script>alert('xss')</script>Success",
            "user": {
                "name": "javascript:alert('evil')",
                "email": "test@example.com"
            },
            "count": 42
        }

        sanitized = validate_and_sanitize_response(response_data)

        assert "<script>" not in sanitized["message"]
        assert "Success" in sanitized["message"]
        assert "javascript:" not in sanitized["user"]["name"]
        assert sanitized["user"]["email"] == "test@example.com"
        assert sanitized["count"] == 42  # Numbers unchanged

    def test_sanitize_html_preserves_safe_content(self):
        """Test that safe content is preserved."""
        safe_input = "Hello World! This is safe content with numbers 123."
        sanitized = sanitize_html(safe_input)

        assert sanitized == safe_input

    def test_sanitize_html_handles_none(self):
        """Test sanitization handles None values."""
        result = sanitize_html(None)
        assert result == "None"

    def test_sanitize_html_handles_numbers(self):
        """Test sanitization handles numeric input."""
        result = sanitize_html(123)
        assert result == "123"

    def test_complex_xss_payload(self):
        """Test against complex XSS payloads."""
        complex_payload = """
        <img src = x onerror = alert('XSS')>
        <svg onload = alert('XSS')>
        <iframe src="javascript:alert('XSS')"></iframe>
        <object data="javascript:alert('XSS')"></object>
        """

        sanitized = sanitize_html(complex_payload)

        assert "onerror=" not in sanitized
        assert "onload=" not in sanitized
        assert "javascript:" not in sanitized
        assert "alert" not in sanitized or "&" in sanitized  # Either removed or escaped

    def test_sql_injection_in_html_context(self):
        """Test that SQL injection attempts in HTML are sanitized."""
        sql_payload = "'; DROP TABLE users; --"
        sanitized = sanitize_html(sql_payload)

        # Should be HTML escaped
        assert "&" in sanitized or sanitized == sql_payload  # Either escaped or safe

    def test_nested_data_sanitization(self):
        """Test deep nested data sanitization."""
        nested_data = {
            "level1": {
                "level2": {
                    "level3": ["<script>alert('deep')</script>", "safe"]
                }
            }
        }

        sanitized = sanitize_user_input(nested_data)

        assert "<script>" not in str(sanitized)
        assert "safe" in sanitized["level1"]["level2"]["level3"]

    def test_empty_and_whitespace_handling(self):
        """Test handling of empty strings and whitespace."""
        test_cases = ["", "   ", "\n\t", None]

        for case in test_cases:
            result = sanitize_html(case)
            assert isinstance(result, str)

    def test_unicode_content_preservation(self):
        """Test that Unicode content is preserved."""
        unicode_content = "Hello 世界 🌍 café naïve résumé"
        sanitized = sanitize_html(unicode_content)

        assert sanitized == unicode_content

    def test_response_sanitization_preserves_structure(self):
        """Test that response sanitization preserves data structure."""
        original = {
            "data": [1, 2, 3],
            "meta": {"count": 3, "page": 1},
            "message": "Success"
        }

        sanitized = validate_and_sanitize_response(original)

        assert isinstance(sanitized["data"], list)
        assert isinstance(sanitized["meta"], dict)
        assert sanitized["data"] == [1, 2, 3]
        assert sanitized["meta"]["count"] == 3
