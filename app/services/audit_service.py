"""Audit logging for compliance."""

from datetime import datetime
from typing import Any, Dict

from app.core.logging import get_logger

logger = get_logger(__name__)


class AuditService:
    """Audit logging for GDPR compliance."""

    def __init__(self):
        self.audit_log = []

    async def log_action(self, user_id: str, action: str, resource: str, details: Dict[str, Any] = None):
        """Log user action."""
        entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "user_id": user_id,
            "action": action,
            "resource": resource,
            "details": details or {},
        }
        self.audit_log.append(entry)
        logger.info(f"Audit: {action} on {resource} by {user_id}")

    async def get_user_audit_log(self, user_id: str) -> list:
        """Get audit log for user."""
        return [entry for entry in self.audit_log if entry["user_id"] == user_id]

    async def export_audit_log(self, user_id: str) -> Dict:
        """Export user data for GDPR."""
        return {
            "user_id": user_id,
            "audit_log": await self.get_user_audit_log(user_id),
            "export_date": datetime.utcnow().isoformat(),
        }

    async def delete_user_data(self, user_id: str):
        """Delete user data for GDPR right to be forgotten."""
        self.audit_log = [entry for entry in self.audit_log if entry["user_id"] != user_id]
        logger.info(f"User data deleted: {user_id}")


audit_service = AuditService()
