"""Admin notification model for real-time alerts."""

from sqlalchemy import JSON, Boolean, Column, String
from sqlalchemy.dialects.postgresql import JSONB as PostgresJSONB

from app.models.base import BaseModel

# Use cross-dialect JSONB (Postgres) / JSON (SQLite)
JSONB = JSON().with_variant(PostgresJSONB, "postgresql")


class AdminNotification(BaseModel):
    """
    Model for storing notifications and alerts specifically for admin users.
    Used for price change alerts, system health warnings, etc.
    """

    __tablename__ = "admin_notifications"

    admin_id = Column(String, index=True)  # Can be specific admin ID or null for all
    notification_type = Column(
        String(50), nullable=False, index=True
    )  # verification_alert, price_change, system_alert
    title = Column(String(255), nullable=False)
    message = Column(String, nullable=False)
    severity = Column(String(20), default="info")  # info, warning, critical
    is_read = Column(Boolean, default=False, index=True)
    metadata_json = Column(JSONB)

    def __repr__(self):
        return f"<AdminNotification(type='{self.notification_type}', severity='{self.severity}')>"
