from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

import pytest

from app.utils.sanitization import (
    sanitize_email_content,
    sanitize_filename,
    sanitize_html,
    sanitize_user_input,
    validate_and_sanitize_response,
)
from app.utils.sql_safety import (
    SQLSafetyValidator,
    audit_query_safety,
    validate_identifier,
    validate_sort_field,
    validate_sort_order,
)


def test_sanitize_html():
    scr = "<script>alert(1)</script>Hello"
    assert sanitize_html(scr) == "&lt;script&gt;alert(1)&lt;/script&gt;Hello"
    assert sanitize_html("javascript:alert(1)") == "alert(1)"
    assert sanitize_html("onclick=alert(1)") == "alert(1)"


def test_sanitize_user_input():
    data = {
        "text": "<p>Hi</p>",
        "list": ["<script>", 123],
        "nested": {"key": "javascript:void(0)"},
    }
    sanitized = sanitize_user_input(data)
    assert sanitized["text"] == "&lt;p&gt;Hi&lt;/p&gt;"
    assert sanitized["list"][0] == "&lt;script&gt;"
    assert sanitized["nested"]["key"] == "void(0)"


def test_sanitize_email_content():
    content = "<h1>Title</h1><script>alert(1)</script>"
    # h1 is allowed
    sanitized = sanitize_email_content(content)
    assert "<h1>" in sanitized
    assert "</h1>" in sanitized
    assert "&lt;script&gt;" in sanitized


def test_validate_and_sanitize_response():
    resp = {"message": "<script>", "id": 1}
    sanitized = validate_and_sanitize_response(resp)
    assert sanitized["message"] == "&lt;script&gt;"
    assert sanitized["id"] == 1


def test_sanitize_filename():
    assert sanitize_filename("../../../etc/passwd") == "passwd"
    assert sanitize_filename("file name with spaces.txt") == "filenamewithspaces.txt"
    assert sanitize_filename("") == "unnamed_file"
    assert sanitize_filename(None) == "unnamed_file"


def test_timezone_utils():
    from app.utils.timezone_utils import (
        days_ago,
        ensure_timezone_aware,
        format_datetime,
        from_utc,
        get_end_of_day,
        get_iso_timestamp,
        get_start_of_day,
        get_timestamp_filename,
        hours_ago,
        minutes_ago,
        parse_date_string,
        safe_datetime_comparison,
        to_utc,
        utc_now,
    )

    now = utc_now()
    assert now.tzinfo == timezone.utc

    naive = datetime.now()
    aware = ensure_timezone_aware(naive)
    assert aware.tzinfo == timezone.utc

    assert to_utc(naive).tzinfo == timezone.utc
    assert to_utc(aware).tzinfo == timezone.utc

    fmt = format_datetime(now)
    assert isinstance(fmt, str)

    # Test local time conversion
    ny = ZoneInfo("America/New_York")
    local = from_utc(now, ny)
    assert local.tzinfo == ny
    assert from_utc(now, None) == now

    dt = parse_date_string("2024-01-01")
    assert dt.year == 2024
    assert dt.tzinfo == timezone.utc

    assert get_start_of_day(now).hour == 0
    assert get_end_of_day(now).hour == 23
    assert get_start_of_day(None).hour == 0
    assert get_end_of_day(None).hour == 23

    assert days_ago(1) < now
    assert hours_ago(1) < now
    assert minutes_ago(1) < now

    assert isinstance(get_timestamp_filename(), str)
    assert get_iso_timestamp() is not None

    assert safe_datetime_comparison(now, now) is True


def test_sql_safety():
    assert validate_identifier("users") == "users"
    with pytest.raises(ValueError):
        validate_identifier("user; drop table")

    assert validate_sort_field("id", ["id", "name"]) == "id"
    with pytest.raises(ValueError):
        validate_sort_field("secrets", ["id", "name"])

    assert validate_sort_order("asc") == "ASC"
    with pytest.raises(ValueError):
        validate_sort_order("invalid")

    assert audit_query_safety("SELECT * FROM users") is True
    assert audit_query_safety("SELECT * FROM users -- comment") is False

    val = SQLSafetyValidator()
    assert val.validate_string_input("safe") == "safe"
    assert val.validate_numeric_input("10", 0, 100) == 10
    assert val.validate_email("test@example.com") == "test@example.com"
