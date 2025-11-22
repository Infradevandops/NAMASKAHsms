"""Alerting and notification service."""
import asyncio
from datetime import datetime
from typing import Dict, List

from app.core.config import settings


class AlertingService:
    """Advanced alerting and notification system."""

    def __init__(self):
        self.alert_channels = {
            "email": True,
            "slack": True,
            "webhook": True,
            "sms": False
        }
        self.alert_rules = {
            "critical": {"cooldown": 300, "escalation": True},
            "warning": {"cooldown": 900, "escalation": False},
            "info": {"cooldown": 1800, "escalation": False}
        }

    async def send_alert(self, alert: Dict) -> bool:
        """Send alert through configured channels."""
        try:
            # Email notification
            if self.alert_channels["email"]:
                await self._send_email_alert(alert)

            # Slack notification
            if self.alert_channels["slack"]:
                await self._send_slack_alert(alert)

            # Webhook notification
            if self.alert_channels["webhook"]:
                await self._send_webhook_alert(alert)

            return True
        except Exception as e:
            print(f"Alert sending failed: {e}")
            return False

    async def _send_email_alert(self, alert: Dict):
        """Send email alert."""
        # Simulate email sending
        print(f"📧 Email Alert: {alert['message']}")

    async def _send_slack_alert(self, alert: Dict):
        """Send Slack alert."""
        # Simulate Slack notification
        emoji = {"critical": "🚨", "warning": "⚠️", "info": "ℹ️"}
        print(f"💬 Slack Alert: {emoji.get(alert['severity'], '📢')} {alert['message']}")

    async def _send_webhook_alert(self, alert: Dict):
        """Send webhook alert."""
        # Simulate webhook call
        print(f"🔗 Webhook Alert: {alert['type']} - {alert['message']}")

    async def process_alert_batch(self, alerts: List[Dict]) -> Dict:
        """Process multiple alerts with deduplication."""
        if not alerts:
            return {"sent": 0, "deduplicated": 0}

        # Group alerts by type and severity
        grouped_alerts = {}
        for alert in alerts:
            key = f"{alert['type']}_{alert['severity']}"
            if key not in grouped_alerts:
                grouped_alerts[key] = []
            grouped_alerts[key].append(alert)

        sent_count = 0
        deduplicated_count = 0

        # Send one alert per group
        for group, group_alerts in grouped_alerts.items():
            if len(group_alerts) > 1:
                # Create summary alert
                summary_alert = {
                    "type": group_alerts[0]["type"],
                    "severity": group_alerts[0]["severity"],
                    "message": f"Multiple {group_alerts[0]['type']} alerts ({len(group_alerts)} total)",
                    "timestamp": datetime.utcnow().isoformat(),
                    "details": [alert["message"] for alert in group_alerts]
                }
                await self.send_alert(summary_alert)
                sent_count += 1
                deduplicated_count += len(group_alerts) - 1
            else:
                await self.send_alert(group_alerts[0])
                sent_count += 1

        return {"sent": sent_count, "deduplicated": deduplicated_count}


# Global alerting service instance
alerting_service = AlertingService()
