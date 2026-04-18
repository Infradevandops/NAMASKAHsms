"""Analytics and reporting models."""

from sqlalchemy import JSON, Boolean, Column, Date, DateTime, Float, Integer, String
from sqlalchemy.dialects.postgresql import UUID

from app.models.base import BaseModel


class AnalyticsCache(BaseModel):
    """Pre-computed analytics for faster dashboard loading."""

    __tablename__ = "analytics_cache"

    user_id = Column(String, nullable=False, index=True)
    period_start = Column(Date, nullable=False)
    period_end = Column(Date, nullable=False)
    total_verifications = Column(Integer, default=0)
    successful_verifications = Column(Integer, default=0)
    failed_verifications = Column(Integer, default=0)
    pending_verifications = Column(Integer, default=0)
    total_spent = Column(Float, default=0.0)
    avg_cost = Column(Float, default=0.0)
    success_rate = Column(Float, default=0.0)
    computed_at = Column(DateTime, nullable=False)


class VerificationEvent(BaseModel):
    """Detailed event timeline for verifications."""

    __tablename__ = "verification_events"

    verification_id = Column(String, nullable=False, index=True)
    event_type = Column(
        String, nullable=False
    )  # created, retry, timeout, completed, refunded, cancelled
    event_data = Column(JSON)


class CustomReport(BaseModel):
    """User-defined report templates."""

    __tablename__ = "custom_reports"

    user_id = Column(String, nullable=False, index=True)
    report_name = Column(String, nullable=False)
    report_type = Column(String, nullable=False)  # daily, weekly, monthly, custom
    filters = Column(JSON)
    schedule = Column(String)  # cron expression
    last_run = Column(DateTime)
    next_run = Column(DateTime, index=True)
    enabled = Column(Boolean, default=True, nullable=False)


class ScheduledReport(BaseModel):
    """Generated reports from scheduled runs."""

    __tablename__ = "scheduled_reports"

    report_id = Column(UUID)
    user_id = Column(String, nullable=False, index=True)
    report_data = Column(JSON)
    generated_at = Column(DateTime, nullable=False)
    sent_at = Column(DateTime)
    status = Column(String, default="pending", nullable=False)  # pending, sent, failed


class UserAnalyticsSnapshot(BaseModel):
    """Historical snapshots for trend analysis."""

    __tablename__ = "user_analytics_snapshots"

    user_id = Column(String, nullable=False, index=True)
    snapshot_date = Column(Date, nullable=False)
    total_verifications = Column(Integer, default=0)
    successful_verifications = Column(Integer, default=0)
    failed_verifications = Column(Integer, default=0)
    total_spent = Column(Float, default=0.0)
    avg_cost = Column(Float, default=0.0)
    success_rate = Column(Float, default=0.0)
    top_service = Column(String)
    top_carrier = Column(String)


class VerificationStatistics(BaseModel):
    """Platform-wide daily statistics."""

    __tablename__ = "verification_statistics"

    stat_date = Column(Date, nullable=False, unique=True, index=True)
    total_verifications = Column(Integer, default=0)
    successful_verifications = Column(Integer, default=0)
    failed_verifications = Column(Integer, default=0)
    total_revenue = Column(Float, default=0.0)
    avg_cost = Column(Float, default=0.0)
    unique_users = Column(Integer, default=0)
    top_service = Column(String)
    top_country = Column(String)
    computed_at = Column(DateTime, nullable=False)
