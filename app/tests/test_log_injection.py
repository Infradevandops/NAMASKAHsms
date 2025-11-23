"""Tests for log injection prevention."""
from app.utils.log_sanitization import (
    sanitize_log_input,
    sanitize_user_id,
    sanitize_service_name,
    create_safe_log_context,
    safe_log_format
)


class TestLogInjectionPrevention:
    """Test log injection prevention utilities."""

    def test_sanitize_log_input_newlines(self):
        """Test that newlines are removed from log input."""
        malicious_input = "Normal text\nFAKE LOG ENTRY: Admin login successful\r\nAnother fake entry"
        sanitized = sanitize_log_input(malicious_input)

        assert "\n" not in sanitized
        assert "\r" not in sanitized
        assert "Normal text" in sanitized
        assert "FAKE LOG ENTRY" in sanitized  # Content preserved but newlines removed

    def test_sanitize_log_input_control_chars(self):
        """Test that control characters are removed."""
        malicious_input = "Text with\x00null\x1bESC\x7fDEL characters"
        sanitized = sanitize_log_input(malicious_input)

        assert "\x00" not in sanitized
        assert "\x1b" not in sanitized
        assert "\x7" not in sanitized
        assert "Text with" in sanitized

    def test_sanitize_log_input_ansi_escape(self):
        """Test that ANSI escape sequences are removed."""
        malicious_input = "Normal text\x1b[31mRed text\x1b[0mNormal again"
        sanitized = sanitize_log_input(malicious_input)

        assert "\x1b[31m" not in sanitized
        assert "\x1b[0m" not in sanitized
        assert "Normal text" in sanitized
        assert "Red text" in sanitized

    def test_sanitize_log_input_length_limit(self):
        """Test that long inputs are truncated."""
        long_input = "A" * 1000
        sanitized = sanitize_log_input(long_input)

        assert len(sanitized) <= 520  # 500 + "[truncated]"
        assert sanitized.endswith("...[truncated]")

    def test_sanitize_user_id(self):
        """Test user ID sanitization."""
        test_cases = [
            ("user123", "user123"),
            ("user - 123_test", "user - 123_test"),
            ("user@domain.com", "user_domain.com"),
            ("user\nid", "user_id"),
            ("", "unknown"),
            (None, "unknown")
        ]

        for input_val, expected in test_cases:
            result = sanitize_user_id(input_val)
            assert result == expected

    def test_sanitize_service_name(self):
        """Test service name sanitization."""
        test_cases = [
            ("telegram", "telegram"),
            ("whatsapp - business", "whatsapp - business"),
            ("service@test", "service_test"),
            ("service\nname", "service_name"),
            ("", "unknown"),
            (None, "unknown")
        ]

        for input_val, expected in test_cases:
            result = sanitize_service_name(input_val)
            assert result == expected

    def test_create_safe_log_context(self):
        """Test safe log context creation."""
        context = create_safe_log_context(
            user_id="user\n123",
            service="telegram\rtest",
            message="Normal\nmessage",
            count=42
        )

        assert context["user_id"] == "user_123"
        assert context["service"] == "telegram_test"
        assert "\n" not in context["message"]
        assert "\r" not in context["message"]
        assert context["count"] == "42"

    def test_safe_log_format(self):
        """Test safe log message formatting."""
        message = safe_log_format(
            "User action\nfake log",
            user_id="user\n123",
            action="login\rtest"
        )

        assert "\n" not in message
        assert "\r" not in message
        assert "User action" in message
        assert "user_id = user_123" in message
        assert "action = login_test" in message

    def test_sanitize_log_input_none_values(self):
        """Test handling of None values."""
        result = sanitize_log_input(None)
        assert result == "None"

    def test_sanitize_log_input_non_string(self):
        """Test handling of non - string values."""
        test_cases = [
            (123, "123"),
            ({"key": "value"}, "{'key': 'value'}"),
            ([1, 2, 3], "[1, 2, 3]")
        ]

        for input_val, expected in test_cases:
            result = sanitize_log_input(input_val)
            assert result == expected

    def test_log_injection_attack_scenarios(self):
        """Test against common log injection attack scenarios."""
        attack_scenarios = [
            "Normal request\n2024 - 01-01 ADMIN LOGIN SUCCESS user = attacker",
            "Request\r\nERROR: Database compromised by user = victim",
            "Data\x1b[2J\x1b[HClearing screen attack",
            "Input\x00NULL byte injection",
            "Text\t\tTab injection for formatting"
        ]

        for attack in attack_scenarios:
            sanitized = sanitize_log_input(attack)

            # Should not contain dangerous characters
            assert "\n" not in sanitized
            assert "\r" not in sanitized
            assert "\x1b" not in sanitized
            assert "\x00" not in sanitized

            # Should preserve readable content
            assert len(sanitized) > 0

    def test_structured_logging_safety(self):
        """Test that structured logging context is safe."""
        unsafe_data = {
            "user_input": "malicious\nlog injection",
            "user_id": "user\r123",
            "service": "test\x1bservice",
            "count": 42
        }

        safe_context = create_safe_log_context(**unsafe_data)

        # All values should be strings and safe
        for key, value in safe_context.items():
            assert isinstance(value, str)
            assert "\n" not in value
            assert "\r" not in value
            assert "\x1b" not in value

    def test_long_user_id_truncation(self):
        """Test that long user IDs are truncated."""
        long_user_id = "user_" + "a" * 100
        sanitized = sanitize_user_id(long_user_id)

        assert len(sanitized) <= 53  # 50 + "..."
        assert sanitized.endswith("...")

    def test_empty_string_handling(self):
        """Test handling of empty strings."""
        assert sanitize_log_input("") == ""
        assert sanitize_user_id("") == "unknown"
        assert sanitize_service_name("") == "unknown"

    def test_unicode_preservation(self):
        """Test that Unicode characters are preserved."""
        unicode_input = "User: José María 中文 🚀"
        sanitized = sanitize_log_input(unicode_input)

        assert "José María" in sanitized
        assert "中文" in sanitized
        assert "🚀" in sanitized
