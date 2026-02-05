"""Audit logging for secrets access and management."""


import json
import logging
from datetime import datetime
from enum import Enum
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


class AuditAction(str, Enum):

    """Audit action types."""

    GET = "get"
    SET = "set"
    DELETE = "delete"
    ROTATE = "rotate"
    LIST = "list"
    INVALIDATE_CACHE = "invalidate_cache"


class SecretsAudit:

    """Audit logging for secrets operations."""

    def __init__(self):

        self.audit_logger = logging.getLogger("secrets_audit")
        self.audit_logger.setLevel(logging.INFO)

    def log_action(

        self,
        action: AuditAction,
        secret_name: str,
        user_id: Optional[str] = None,
        ip_address: Optional[str] = None,
        status: str = "success",
        error: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        ):
        """Log secrets operation for audit trail."""
        audit_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "action": action.value,
            "secret_name": secret_name,
            "user_id": user_id or "system",
            "ip_address": ip_address or "unknown",
            "status": status,
            "error": error,
            "metadata": metadata or {},
        }

        self.audit_logger.info(json.dumps(audit_entry))

    def log_get(

        self,
        secret_name: str,
        user_id: Optional[str] = None,
        ip_address: Optional[str] = None,
        cached: bool = False,
        ):
        """Log secret retrieval."""
        self.log_action(
            action=AuditAction.GET,
            secret_name=secret_name,
            user_id=user_id,
            ip_address=ip_address,
            metadata={"cached": cached},
        )

    def log_set(

        self,
        secret_name: str,
        user_id: Optional[str] = None,
        ip_address: Optional[str] = None,
        created: bool = False,
        ):
        """Log secret creation or update."""
        self.log_action(
            action=AuditAction.SET,
            secret_name=secret_name,
            user_id=user_id,
            ip_address=ip_address,
            metadata={"created": created},
        )

    def log_delete(

        self,
        secret_name: str,
        user_id: Optional[str] = None,
        ip_address: Optional[str] = None,
        recovery_window_days: int = 7,
        ):
        """Log secret deletion."""
        self.log_action(
            action=AuditAction.DELETE,
            secret_name=secret_name,
            user_id=user_id,
            ip_address=ip_address,
            metadata={"recovery_window_days": recovery_window_days},
        )

    def log_rotate(

        self,
        secret_name: str,
        user_id: Optional[str] = None,
        ip_address: Optional[str] = None,
        ):
        """Log secret rotation."""
        self.log_action(
            action=AuditAction.ROTATE,
            secret_name=secret_name,
            user_id=user_id,
            ip_address=ip_address,
        )

    def log_error(

        self,
        action: AuditAction,
        secret_name: str,
        error: str,
        user_id: Optional[str] = None,
        ip_address: Optional[str] = None,
        ):
        """Log failed secrets operation."""
        self.log_action(
            action=action,
            secret_name=secret_name,
            user_id=user_id,
            ip_address=ip_address,
            status="error",
            error=error,
        )


# Global audit instance
        _audit: Optional[SecretsAudit] = None


    def get_audit() -> SecretsAudit:

        """Get or create global audit instance."""
        global _audit

        if _audit is None:
        _audit = SecretsAudit()

        return _audit
