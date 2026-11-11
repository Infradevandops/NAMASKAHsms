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
                summary["message"] = (
                    f"{len(group_alerts)} similar alerts: {group_alerts[0]['message']}"
                )
                await self.send_alert(summary)
                deduped += len(group_alerts) - 1
            else:
                await self.send_alert(group_alerts[0])
            sent += 1

        return {"sent": sent, "deduplicated": deduped}

    async def send_margin_alert(
        self, margin_pct: float, revenue: float, tv_cost: float
    ) -> None:
        await self.send_alert(
            {
                "type": "margin_below_threshold",
                "severity": "critical",
                "message": (
                    f"TextVerified margin is {margin_pct:.1f}% this week — below 15% threshold. "
                    f"Platform revenue: ${revenue:.2f} | TV cost: ${tv_cost:.2f}. "
                    "Check TextVerified pricing or billing immediately."
                ),
            }
        )

    async def send_target_miss_alert(
        self, month: str, actual: float, target: float
    ) -> None:
        shortfall = target - actual
        await self.send_alert(
            {
                "type": "monthly_target_missed",
                "severity": "warning",
                "message": (
                    f"Month {month} closed below revenue target. "
                    f"Actual: ${actual:.2f} | Target: ${target:.2f} | Shortfall: ${shortfall:.2f}."
                ),
            }
        )

    async def send_stock_depleted_alert(self, service_name: str, watcher_count: int) -> None:
        """Fire when a service transitions available → unavailable during stock monitor loop."""
        await self.send_alert(
            {
                "type": "stock_depleted",
                "severity": "warning",
                "message": (
                    f"⚠️ {service_name} is now out of stock on TextVerified. "
                    f"{watcher_count} user(s) are watching this service. "
                    "Check TV dashboard or contact TV support if this persists."
                ),
            }
        )

    async def send_back_order_queue_alert(self, service_name: str, queue_depth: int) -> None:
        """Fire when back-order queue for a rental service exceeds 5 users."""
        if queue_depth < 5:
            return
        await self.send_alert(
            {
                "type": "back_order_queue_depth",
                "severity": "info",
                "message": (
                    f"📦 Back-order queue for {service_name} has {queue_depth} users waiting. "
                    "Consider contacting TV to prioritise inventory for this service."
                ),
            }
        )

    async def send_rental_expiry_digest(self, expiring_rentals: list) -> None:
        """Daily digest of rentals expiring in next 24h. Batched — one email, not per-rental."""
        if not expiring_rentals:
            return
        lines = "".join(
            f"<li>{r['service_name']} — user {r['user_email']} — expires {r['ends_at']}</li>"
            for r in expiring_rentals
        )
        await self.send_alert(
            {
                "type": "rental_expiry_batch",
                "severity": "info",
                "message": (
                    f"🗓️ {len(expiring_rentals)} rental(s) expire in the next 24 hours. "
                    f"<ul>{lines}</ul>"
                ),
            }
        )


alerting_service = AlertingService()
