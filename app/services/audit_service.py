from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from app.core.logging import get_logger
from app.models.audit_log import AuditLog

logger = get_logger(__name__)


class AuditService:
    """Institutional Audit Logging Service."""

    def __init__(self, db: Session):
        self.db = db

    async def log_action(
        self,
        user_id: str,
        action: str,
        resource_type: str,
        resource_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> AuditLog:
        """Persist administrative or security action to the audit log."""
        log_entry = AuditLog(
            user_id=user_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            ip_address=ip_address,
            user_agent=user_agent,
            details=details or {},
        )

        self.db.add(log_entry)
        self.db.commit()
        self.db.refresh(log_entry)

        logger.info(f"Audit Log Created: {action} on {resource_type} by User:{user_id}")
        return log_entry

    async def get_system_audit_logs(
        self, limit: int = 100, offset: int = 0
    ) -> List[AuditLog]:
        """Fetch global audit logs for administrative review."""
        query = (
            select(AuditLog)
            .order_by(desc(AuditLog.created_at))
            .offset(offset)
            .limit(limit)
        )
        return self.db.execute(query).scalars().all()

    async def fetch_user_history(self, user_id: str, limit: int = 50) -> List[AuditLog]:
        """Fetch audit trail for a specific user ID."""
        query = (
            select(AuditLog)
            .where(AuditLog.user_id == user_id)
            .order_by(desc(AuditLog.created_at))
            .limit(limit)
        )
        return self.db.execute(query).scalars().all()

    async def export_forensic_log(self, days: int = 30) -> List[Dict[str, Any]]:
        """Export audit logs in a forensic-ready format."""
        logs = await self.get_system_audit_logs(limit=1000)
        return [
            {
                "timestamp": l.created_at.isoformat(),
                "user_id": l.user_id,
                "action": l.action,
                "resource": f"{l.resource_type}:{l.resource_id or 'N/A'}",
                "details": l.details,
            }
            for l in logs
        ]
