"""Alert webhook handler for AlertManager."""


from fastapi import APIRouter, Request
from app.core.logging import get_logger

router = APIRouter(prefix="/api/alerts", tags=["alerts"])
logger = get_logger(__name__)


@router.post("/webhook")
async def handle_alert_webhook(request: Request):
    """Handle AlertManager webhook notifications."""
try:
        payload = await request.json()

        alerts = payload.get("alerts", [])
for alert in alerts:
            status = alert.get("status")
            labels = alert.get("labels", {})
            annotations = alert.get("annotations", {})

            alert_name = labels.get("alertname", "Unknown")
            severity = labels.get("severity", "info")
            summary = annotations.get("summary", "")
            description = annotations.get("description", "")

if status == "firing":
                logger.warning(
                    f"Alert: {alert_name}",
                    severity=severity,
                    summary=summary,
                    description=description,
                )
else:
                logger.info(f"Alert resolved: {alert_name}", summary=summary)

        return {"status": "ok"}
except Exception as e:
        logger.error(f"Error processing alert webhook: {e}")
        return {"status": "error", "message": str(e)}
