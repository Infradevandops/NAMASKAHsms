"""System monitoring and support - related database models."""


from sqlalchemy import Boolean, Column, DateTime, Float, String
from app.models.base import BaseModel

class ServiceStatus(BaseModel):

    """Service health monitoring."""

    __tablename__ = "service_status"

    service_name = Column(String, nullable=False, index=True)
    status = Column(String, default="operational", nullable=False)
    success_rate = Column(Float, default=100.0, nullable=False)
    last_checked = Column(DateTime, nullable=False, index=True)


class SupportTicket(BaseModel):

    """Customer support tickets."""

    __tablename__ = "support_tickets"

    user_id = Column(String, index=True)
    name = Column(String, nullable=False)
    email = Column(String, nullable=False)
    category = Column(String, nullable=False)
    message = Column(String, nullable=False)
    status = Column(String, default="open", nullable=False, index=True)
    admin_response = Column(String)


class ActivityLog(BaseModel):

    """User activity tracking."""

    __tablename__ = "activity_logs"

    user_id = Column(String, index=True)
    email = Column(String)
    page = Column(String)
    action = Column(String, nullable=False)
    element = Column(String)
    status = Column(String, nullable=False)
    details = Column(String)
    error_message = Column(String)
    ip_address = Column(String)
    user_agent = Column(String)


class BannedNumber(BaseModel):

    """Banned phone numbers tracking."""

    __tablename__ = "banned_numbers"

    phone_number = Column(String, nullable=False, index=True)
    service_name = Column(String, nullable=False, index=True)
    area_code = Column(String)
    carrier = Column(String)
    fail_count = Column(Float, default=1, nullable=False)
    last_failed_at = Column(DateTime, nullable=False)


class InAppNotification(BaseModel):

    """In - app notifications."""

    __tablename__ = "in_app_notifications"

    user_id = Column(String, nullable=False, index=True)
    title = Column(String, nullable=False)
    message = Column(String, nullable=False)
    type = Column(String, default="receipt", nullable=False)
    is_read = Column(Boolean, default=False, nullable=False, index=True)
    verification_id = Column(String)