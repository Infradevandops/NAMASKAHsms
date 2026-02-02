

from datetime import timezone
from app.utils.sanitization import sanitize_html
from app.utils.sql_safety import SQLSafetyValidator, audit_query_safety
from app.utils.timezone_utils import format_datetime, parse_date_string, utc_now

class TestUtilsComplete:

    """Tests for utility functions."""

    def test_timezone_utils(self):

        """Test timezone utility functions."""
        now = utc_now()
        assert now.tzinfo == timezone.utc

        dt_str = format_datetime(now)
        assert isinstance(dt_str, str)

        parsed = parse_date_string(now.strftime("%Y-%m-%d"))
        assert parsed.year == now.year
        assert parsed.month == now.month
        assert parsed.day == now.day

    def test_sql_safety_utils(self):

        """Test SQL safety utility functions."""
        safe_input = "normal_user_123"
        assert SQLSafetyValidator.validate_string_input(safe_input) == safe_input

        unsafe_query = "SELECT * FROM users WHERE name = '' ; DROP TABLE users"
        assert audit_query_safety(unsafe_query) is False

        safe_query = "SELECT * FROM users WHERE id = :id"
        assert audit_query_safety(safe_query) is True

    def test_sanitization_utils(self):

        """Test HTML and string sanitization."""
        html = "<p>Hello <script>alert('xss')</script></p>"
        sanitized = sanitize_html(html)
        assert "<script>" not in sanitized

        text = "Hello\x00World"
        assert SQLSafetyValidator.validate_string_input(text) == "HelloWorld"