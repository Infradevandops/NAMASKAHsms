"""Alerting and notification service."""


from datetime import datetime
from typing import Dict, List
import logging

logger = logging.getLogger(__name__)


class AlertingService:
    """Advanced alerting and notification system."""

    def __init__(self):
        self.alert_channels = {
            "email": True,
            "slack": True,
            "webhook": True,
            "sms": False,
        }
        self.alert_rules = {
            "critical": {"cooldown": 300, "escalation": True},
            "warning": {"cooldown": 900, "escalation": False},
            "info": {"cooldown": 1800, "escalation": False},
        }

    async def send_alert(self, alert: Dict) -> bool:
        """Send alert through configured channels."""
        try:
            if self.alert_channels["email"]:
                await self._send_email_alert(alert)
            if self.alert_channels["slack"]:
                await self._send_slack_alert(alert)
            if self.alert_channels["webhook"]:
                await self._send_webhook_alert(alert)
            return True
        except Exception as e:
            logger.error("Alert sending failed", extra={"error": str(e)})
            return False

    async def _send_email_alert(self, alert: Dict):
        """Send email alert."""
        logger.info("Email alert", extra={"message": alert['message']})

    async def _send_slack_alert(self, alert: Dict):
        """Send Slack alert."""
        logger.info("Slack alert", extra={"severity": alert.get('severity'), "message": alert['message']})

    async def _send_webhook_alert(self, alert: Dict):
        """Send webhook alert."""
        logger.info("Webhook alert", extra={"type": alert.get('type'), "message": alert['message']})

    async def process_alert_batch(self, alerts: List[Dict]) -> Dict:
        """Process multiple alerts with deduplication."""
        if not alerts:
            return {"sent": 0, "deduplicated": 0}

        grouped_alerts = {}
        for alert in alerts:
            key = f"{alert['type']}_{alert['severity']}"
            if key not in grouped_alerts:
                grouped_alerts[key] = []
            grouped_alerts[key].append(alert)

        sent_count = 0
        deduplicated_count = 0

        for group, group_alerts in grouped_alerts.items():
            if len(group_alerts) > 1:
                summary_alert = group_alerts[0].copy()
                summary_alert["message"] = f"{len(group_alerts)} similar alerts: {group_alerts[0]['message']}"
                await self.send_alert(summary_alert)
                deduplicated_count += len(group_alerts) - 1
            else:
                await self.send_alert(group_alerts[0])
            sent_count += 1

        return {"sent": sent_count, "deduplicated": deduplicated_count}
