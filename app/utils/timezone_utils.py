"""Timezone utilities for consistent datetime handling across the application."""

from datetime import datetime, timezone, timedelta

from typing import Optional, Union
from zoneinfo import ZoneInfo


def utc_now() -> datetime:
    """Get current UTC datetime."""
    return datetime.now(timezone.utc)


def to_utc(dt: datetime) -> datetime:
    """Convert datetime to UTC."""
    if dt.tzinfo is None:
        # Assume naive datetime is UTC
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def from_utc(dt: datetime, target_tz: Union[str, timezone] = None) -> datetime:
    """Convert UTC datetime to target timezone."""
    if target_tz is None:
        return dt

    if isinstance(target_tz, str):
        target_tz = ZoneInfo(target_tz)

    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)

    return dt.astimezone(target_tz)


def parse_date_string(date_str: str, format_str: str = "%Y-%m-%d") -> datetime:
    """Parse date string and return timezone - aware datetime."""
    dt = datetime.strptime(date_str, format_str)
    return dt.replace(tzinfo=timezone.utc)


def format_datetime(dt: datetime, format_str: str = "%Y-%m-%d %H:%M:%S UTC") -> str:
    """Format datetime as string with timezone info."""
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.strftime(format_str)


def get_start_of_day(dt: Optional[datetime] = None) -> datetime:
    """Get start of day in UTC."""
    if dt is None:
        dt = utc_now()
    return dt.replace(hour=0, minute=0, second=0, microsecond=0)


def get_end_of_day(dt: Optional[datetime] = None) -> datetime:
    """Get end of day in UTC."""
    if dt is None:
        dt = utc_now()
    return dt.replace(hour=23, minute=59, second=59, microsecond=999999)


def days_ago(days: int) -> datetime:
    """Get datetime N days ago in UTC."""
    return utc_now() - timedelta(days=days)


def hours_ago(hours: int) -> datetime:
    """Get datetime N hours ago in UTC."""
    return utc_now() - timedelta(hours=hours)


def minutes_ago(minutes: int) -> datetime:
    """Get datetime N minutes ago in UTC."""
    return utc_now() - timedelta(minutes=minutes)


def is_timezone_aware(dt: datetime) -> bool:
    """Check if datetime is timezone - aware."""
    return dt.tzinfo is not None and dt.tzinfo.utcoffset(dt) is not None


def ensure_timezone_aware(dt: datetime) -> datetime:
    """Ensure datetime is timezone - aware (assume UTC if naive)."""
    if not is_timezone_aware(dt):
        return dt.replace(tzinfo=timezone.utc)
    return dt


def get_timestamp_filename() -> str:
    """Get timestamp string for filenames."""
    return utc_now().strftime("%Y%m%d_%H%M%S")


def get_iso_timestamp() -> str:
    """Get ISO format timestamp."""
    return utc_now().isoformat()


def safe_datetime_comparison(dt1: datetime, dt2: datetime) -> bool:
    """Safely compare two datetimes, ensuring both are timezone - aware."""
    dt1 = ensure_timezone_aware(dt1)
    dt2 = ensure_timezone_aware(dt2)
    return dt1 == dt2
