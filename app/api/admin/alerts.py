"""Alert webhook handler for AlertManager + real admin alerts API."""

from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.core.database import get_db
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
                logger.warning(f"Alert: {alert_name}", severity=severity, summary=summary, description=description)
            else:
                logger.info(f"Alert resolved: {alert_name}", summary=summary)
        return {"status": "ok"}
    except Exception as e:
        logger.error(f"Error processing alert webhook: {e}")
        return {"status": "error", "message": str(e)}


@router.get("/")
async def get_alerts(db: Session = Depends(get_db)):
    """D-025: Return real alert data from DB for admin alerts page."""
    alerts = []
    now = datetime.now(timezone.utc)
    cutoff = now - timedelta(hours=24)

    # Stock depletion alerts from stock_watches
    try:
        from app.models.stock_watch import StockWatch
        from sqlalchemy import func
        depleted = (
            db.query(StockWatch.service_name, func.count(StockWatch.id).label("watchers"))
            .filter(StockWatch.notified_at.is_(None))
            .group_by(StockWatch.service_name)
            .all()
        )
        for row in depleted:
            alerts.append({
                "id": f"stock_{row.service_name}",
                "type": "stock_depleted",
                "severity": "warning",
                "title": f"{row.service_name.title()} out of stock",
                "message": f"{row.watchers} user(s) waiting for {row.service_name}",
                "status": "firing",
                "created_at": now.isoformat(),
            })
    except Exception as e:
        logger.warning(f"Stock watch alert query failed: {e}")

    # Back-order queue alerts
    try:
        from app.models.rental_back_order import RentalBackOrder
        from sqlalchemy import func
        backorders = (
            db.query(RentalBackOrder.service_name, func.count(RentalBackOrder.id).label("count"))
            .filter(RentalBackOrder.fulfilled_at.is_(None))
            .group_by(RentalBackOrder.service_name)
            .having(func.count(RentalBackOrder.id) >= 1)
            .all()
        )
        for row in backorders:
            alerts.append({
                "id": f"backorder_{row.service_name}",
                "type": "back_order_queue",
                "severity": "info",
                "title": f"{row.service_name.title()} back-order queue",
                "message": f"{row.count} rental(s) queued for {row.service_name}",
                "status": "firing",
                "created_at": now.isoformat(),
            })
    except Exception as e:
        logger.warning(f"Back-order alert query failed: {e}")

    return {
        "alerts": alerts,
        "total": len(alerts),
        "critical": sum(1 for a in alerts if a["severity"] == "critical"),
        "warning": sum(1 for a in alerts if a["severity"] == "warning"),
        "info": sum(1 for a in alerts if a["severity"] == "info"),
    }


@router.get("/stock-watches/count")
async def get_stock_watch_count(db: Session = Depends(get_db)):
    """D-024: Total active stock watches across all users."""
    try:
        from app.models.stock_watch import StockWatch
        count = db.query(StockWatch).filter(StockWatch.notified_at.is_(None)).count()
        return {"count": count}
    except Exception:
        return {"count": 0}
