"""Alerting and notification service."""

import logging
from datetime import datetime, timezone
from typing import Dict, List, Optional

from app.core.logging import get_logger

logger = get_logger(__name__)


class AlertingService:
    """Alerting system — email admin on critical business events."""

    async def send_alert(self, alert: Dict) -> bool:
        """Route alert to configured channels (email only for now)."""
        try:
            await self._send_email_alert(alert)
            return True
        except Exception as e:
            logger.error(f"Alert sending failed: {e}")
            return False

    async def _send_email_alert(self, alert: Dict) -> None:
        from app.core.config import get_settings
        from app.services.email_service import email_service

        settings = get_settings()
        admin_email = settings.effective_admin_notify_email
        if not admin_email:
            logger.warning("No admin_notify_email configured — alert dropped")
            return

        severity = alert.get("severity", "info")
        emoji = {"info": "ℹ️", "warning": "⚠️", "critical": "🚨"}.get(severity, "ℹ️")
        subject = f"{emoji} [{severity.upper()}] {alert.get('type', 'Alert')} — Vrenum"
        html = (
            f"<h2>{emoji} {alert.get('type', 'System Alert')}</h2>"
            f"<p>{alert.get('message', '')}</p>"
            f"<p style='color:#9ca3af;font-size:12px;'>Severity: {severity} · "
            f"{datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}</p>"
        )
        await email_service._send(admin_email, subject, html)
        logger.info(f"Alert emailed to {admin_email}: {alert.get('message', '')}")

    async def check_revenue_zero(self, db) -> bool:
        """Fire a critical alert if today's revenue is $0 at or after 18:00 UTC.
        Returns True if alert was fired.
        """
        now = datetime.now(timezone.utc)
        if now.hour < 18:
            return False

        try:
            from sqlalchemy import text

            result = db.execute(
                text(
                    "SELECT COALESCE(SUM(amount), 0) FROM transactions "
                    "WHERE type = 'credit' AND created_at >= CURRENT_DATE"
                )
            ).scalar()
            if float(result or 0) == 0.0:
                await self.send_alert(
                    {
                        "type": "revenue_zero",
                        "severity": "critical",
                        "message": (
                            f"No revenue recorded today ({now.strftime('%Y-%m-%d')}). "
                            "Paystack webhook may be down or payment flow is broken."
                        ),
                    }
                )
                return True
        except Exception as e:
            logger.error(f"Revenue-zero check failed: {e}")
        return False

    async def process_alert_batch(self, alerts: List[Dict]) -> Dict:
        """Process multiple alerts with deduplication."""
        if not alerts:
            return {"sent": 0, "deduplicated": 0}

        grouped: Dict[str, List] = {}
        for alert in alerts:
            key = f"{alert['type']}_{alert.get('severity', 'info')}"
            grouped.setdefault(key, []).append(alert)

        sent = 0
        deduped = 0
        for group_alerts in grouped.values():
            if len(group_alerts) > 1:
                summary = group_alerts[0].copy()
                summary[
                    "message"
                ] = f"{len(group_alerts)} similar alerts: {group_alerts[0]['message']}"
                await self.send_alert(summary)
                deduped += len(group_alerts) - 1
            else:
                await self.send_alert(group_alerts[0])
            sent += 1

        return {"sent": sent, "deduplicated": deduped}


alerting_service = AlertingService()
