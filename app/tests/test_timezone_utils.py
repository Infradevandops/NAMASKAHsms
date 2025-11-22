"""Test suite for timezone utilities."""
import pytest
from datetime import datetime, timezone
import pytz

from app.utils.timezone_utils import (
    utc_now,
    to_utc,
    from_utc,
    parse_date_string,
    format_datetime,
    get_start_of_day,
    get_end_of_day,
    days_ago,
    hours_ago,
    minutes_ago,
    is_timezone_aware,
    ensure_timezone_aware,
    get_timestamp_filename,
    get_iso_timestamp,
    safe_datetime_comparison
)


class TestTimezoneUtils:
    """Test timezone utility functions."""

    def test_utc_now(self):
        """Test utc_now returns timezone - aware UTC datetime."""
        now = utc_now()
        assert now.tzinfo == timezone.utc
        assert isinstance(now, datetime)

    def test_to_utc_naive_datetime(self):
        """Test converting naive datetime to UTC."""
        naive_dt = datetime(2024, 1, 1, 12, 0, 0)
        utc_dt = to_utc(naive_dt)
        assert utc_dt.tzinfo == timezone.utc
        assert utc_dt.replace(tzinfo=None) == naive_dt

    def test_to_utc_aware_datetime(self):
        """Test converting timezone - aware datetime to UTC."""
        est = pytz.timezone('US/Eastern')
        est_dt = est.localize(datetime(2024, 1, 1, 12, 0, 0))
        utc_dt = to_utc(est_dt)
        assert utc_dt.tzinfo == timezone.utc
        # EST is UTC - 5, so 12:00 EST = 17:00 UTC
        assert utc_dt.hour == 17

    def test_from_utc_to_timezone(self):
        """Test converting UTC to specific timezone."""
        utc_dt = datetime(2024, 1, 1, 17, 0, 0, tzinfo=timezone.utc)
        est_dt = from_utc(utc_dt, 'US/Eastern')
        # UTC 17:00 = EST 12:00 (UTC - 5)
        assert est_dt.hour == 12

    def test_from_utc_none_timezone(self):
        """Test from_utc with None timezone returns original."""
        utc_dt = datetime(2024, 1, 1, 17, 0, 0, tzinfo=timezone.utc)
        result = from_utc(utc_dt, None)
        assert result == utc_dt

    def test_parse_date_string(self):
        """Test parsing date string to timezone - aware datetime."""
        dt = parse_date_string("2024 - 01-01", "%Y-%m-%d")
        assert dt.tzinfo == timezone.utc
        assert dt.year == 2024
        assert dt.month == 1
        assert dt.day == 1

    def test_format_datetime(self):
        """Test formatting datetime with timezone info."""
        dt = datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        formatted = format_datetime(dt)
        assert "2024 - 01-01 12:00:00 UTC" in formatted

    def test_format_datetime_naive(self):
        """Test formatting naive datetime (assumes UTC)."""
        dt = datetime(2024, 1, 1, 12, 0, 0)
        formatted = format_datetime(dt)
        assert "2024 - 01-01 12:00:00 UTC" in formatted

    def test_get_start_of_day(self):
        """Test getting start of day."""
        dt = datetime(2024, 1, 1, 15, 30, 45, tzinfo=timezone.utc)
        start = get_start_of_day(dt)
        assert start.hour == 0
        assert start.minute == 0
        assert start.second == 0
        assert start.microsecond == 0
        assert start.date() == dt.date()

    def test_get_start_of_day_none(self):
        """Test getting start of day with None (uses current day)."""
        start = get_start_of_day(None)
        assert start.hour == 0
        assert start.minute == 0
        assert start.second == 0
        assert start.microsecond == 0

    def test_get_end_of_day(self):
        """Test getting end of day."""
        dt = datetime(2024, 1, 1, 15, 30, 45, tzinfo=timezone.utc)
        end = get_end_of_day(dt)
        assert end.hour == 23
        assert end.minute == 59
        assert end.second == 59
        assert end.microsecond == 999999
        assert end.date() == dt.date()

    def test_get_end_of_day_none(self):
        """Test getting end of day with None (uses current day)."""
        end = get_end_of_day(None)
        assert end.hour == 23
        assert end.minute == 59
        assert end.second == 59
        assert end.microsecond == 999999

    def test_days_ago(self):
        """Test getting datetime N days ago."""
        now = utc_now()
        past = days_ago(7)
        diff = now - past
        assert abs(diff.days - 7) <= 1  # Allow for small timing differences

    def test_hours_ago(self):
        """Test getting datetime N hours ago."""
        now = utc_now()
        past = hours_ago(24)
        diff = now - past
        assert abs(diff.total_seconds() - 24 * 3600) < 60  # Within 1 minute

    def test_minutes_ago(self):
        """Test getting datetime N minutes ago."""
        now = utc_now()
        past = minutes_ago(30)
        diff = now - past
        assert abs(diff.total_seconds() - 30 * 60) < 60  # Within 1 minute

    def test_is_timezone_aware_true(self):
        """Test timezone awareness detection for aware datetime."""
        dt = datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        assert is_timezone_aware(dt) is True

    def test_is_timezone_aware_false(self):
        """Test timezone awareness detection for naive datetime."""
        dt = datetime(2024, 1, 1, 12, 0, 0)
        assert is_timezone_aware(dt) is False

    def test_ensure_timezone_aware_naive(self):
        """Test ensuring timezone awareness for naive datetime."""
        dt = datetime(2024, 1, 1, 12, 0, 0)
        aware_dt = ensure_timezone_aware(dt)
        assert aware_dt.tzinfo == timezone.utc
        assert aware_dt.replace(tzinfo=None) == dt

    def test_ensure_timezone_aware_already_aware(self):
        """Test ensuring timezone awareness for already aware datetime."""
        dt = datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        result = ensure_timezone_aware(dt)
        assert result == dt
        assert result.tzinfo == timezone.utc

    def test_get_timestamp_filename(self):
        """Test getting timestamp for filenames."""
        timestamp = get_timestamp_filename()
        assert len(timestamp) == 15  # YYYYMMDD_HHMMSS
        assert '_' in timestamp
        # Should be parseable as datetime
        datetime.strptime(timestamp, '%Y%m%d_%H%M%S')

    def test_get_iso_timestamp(self):
        """Test getting ISO format timestamp."""
        timestamp = get_iso_timestamp()
        assert 'T' in timestamp
        assert timestamp.endswith('+00:00')  # UTC timezone
        # Should be parseable
        datetime.fromisoformat(timestamp)

    def test_safe_datetime_comparison_both_naive(self):
        """Test safe comparison of two naive datetimes."""
        dt1 = datetime(2024, 1, 1, 12, 0, 0)
        dt2 = datetime(2024, 1, 1, 12, 0, 0)
        assert safe_datetime_comparison(dt1, dt2) is True

    def test_safe_datetime_comparison_both_aware(self):
        """Test safe comparison of two aware datetimes."""
        dt1 = datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        dt2 = datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        assert safe_datetime_comparison(dt1, dt2) is True

    def test_safe_datetime_comparison_mixed(self):
        """Test safe comparison of mixed naive/aware datetimes."""
        dt1 = datetime(2024, 1, 1, 12, 0, 0)  # naive
        dt2 = datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc)  # aware
        assert safe_datetime_comparison(dt1, dt2) is True

    def test_safe_datetime_comparison_different(self):
        """Test safe comparison of different datetimes."""
        dt1 = datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        dt2 = datetime(2024, 1, 1, 13, 0, 0, tzinfo=timezone.utc)
        assert safe_datetime_comparison(dt1, dt2) is False


class TestTimezoneIntegration:
    """Test timezone utilities integration scenarios."""

    def test_date_range_filtering(self):
        """Test date range filtering with timezone - aware dates."""
        start_date = parse_date_string("2024 - 01-01")
        end_date = get_end_of_day(parse_date_string("2024 - 01-31"))

        # Test datetime in range
        test_dt = datetime(2024, 1, 15, 12, 0, 0, tzinfo=timezone.utc)
        assert start_date <= test_dt <= end_date

        # Test datetime out of range
        test_dt_out = datetime(2024, 2, 1, 12, 0, 0, tzinfo=timezone.utc)
        assert not (start_date <= test_dt_out <= end_date)

    def test_analytics_time_window(self):
        """Test analytics time window calculation."""
        now = utc_now()
        thirty_days_ago = days_ago(30)

        # Should be approximately 30 days difference
        diff = now - thirty_days_ago
        assert 29 <= diff.days <= 31

    def test_filename_generation(self):
        """Test consistent filename generation."""
        filename1 = f"export_{get_timestamp_filename()}.csv"
        filename2 = f"backup_{get_timestamp_filename()}.csv"

        assert filename1.startswith("export_")
        assert filename1.endswith(".csv")
        assert filename2.startswith("backup_")
        assert filename2.endswith(".csv")

    def test_cross_timezone_conversion(self):
        """Test converting between different timezones."""
        # Create UTC datetime
        utc_dt = datetime(2024, 6, 15, 14, 0, 0, tzinfo=timezone.utc)

        # Convert to different timezones
        ny_dt = from_utc(utc_dt, 'America/New_York')
        tokyo_dt = from_utc(utc_dt, 'Asia/Tokyo')
        london_dt = from_utc(utc_dt, 'Europe/London')

        # All should represent the same moment in time
        assert to_utc(ny_dt) == utc_dt
        assert to_utc(tokyo_dt) == utc_dt
        assert to_utc(london_dt) == utc_dt


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
