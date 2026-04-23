"""Price history service for snapshots, trends, and alerts."""

from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import Any, Dict, List, Optional

from sqlalchemy import desc, func
from sqlalchemy.orm import Session

from app.core.logging import get_logger
from app.models.admin_notification import AdminNotification
from app.models.price_snapshot import PriceSnapshot
from app.services.provider_price_service import ProviderPriceService

logger = get_logger(__name__)


class PriceHistoryService:
    """Service for managing historical price data and triggering alerts."""

    def __init__(self, db: Session):
        self.db = db
        self.provider_price_service = ProviderPriceService(db)

    async def record_current_prices(self, source: str = "textverified"):
        """
        Fetch current live prices and store them as snapshots in the database.
        Also checks for significant price changes and creates admin notifications.
        """
        logger.info(f"Recording price snapshots from {source}...")
        
        try:
            live_data = await self.provider_price_service.get_live_prices(force_refresh=True)
            prices = live_data.get("prices", [])
            
            new_snapshots = []
            alerts_created = 0
            
            for p in prices:
                # 1. Create snapshot
                snapshot = PriceSnapshot(
                    service_id=p["service_id"],
                    service_name=p["service_name"],
                    provider_cost=Decimal(str(p["provider_cost"])),
                    platform_price=Decimal(str(p["platform_price"])),
                    markup_percentage=Decimal(str(p["markup_percentage"])),
                    currency=p["currency"],
                    source=source,
                    captured_at=datetime.now(timezone.utc)
                )
                new_snapshots.append(snapshot)
                
                # 2. Check for significant price change (compare with last snapshot)
                await self._check_price_change_alert(p, source)
                
            self.db.add_all(new_snapshots)
            self.db.commit()
            
            logger.info(f"Successfully recorded {len(new_snapshots)} price snapshots.")
            return len(new_snapshots)

        except Exception as e:
            logger.error(f"Failed to record price snapshots: {e}")
            self.db.rollback()
            raise

    async def _check_price_change_alert(self, current_price: Dict[str, Any], source: str):
        """Detect >10% price increase and create admin notification."""
        last_snapshot = (
            self.db.query(PriceSnapshot)
            .filter(PriceSnapshot.service_id == current_price["service_id"])
            .order_by(desc(PriceSnapshot.captured_at))
            .first()
        )
        
        if last_snapshot:
            old_cost = float(last_snapshot.provider_cost)
            new_cost = float(current_price["provider_cost"])
            
            if old_cost > 0:
                change_pct = ((new_cost - old_cost) / old_cost) * 100
                
                if change_pct >= 10.0:
                    logger.warning(f"Significant price increase detected for {current_price['service_name']}: {change_pct:.2f}%")
                    
                    notification = AdminNotification(
                        notification_type="price_change",
                        title=f"Price Alert: {current_price['service_name']}",
                        message=f"Provider cost increased by {change_pct:.2f}% (from ${old_cost:.2f} to ${new_cost:.2f})",
                        severity="warning" if change_pct < 25 else "critical",
                        metadata_json={
                            "service_id": current_price["service_id"],
                            "old_cost": old_cost,
                            "new_cost": new_cost,
                            "change_percentage": change_pct,
                            "source": source
                        }
                    )
                    self.db.add(notification)

    def get_price_history(self, service_id: str, days: int = 30) -> List[Dict[str, Any]]:
        """Retrieve historical price snapshots for a specific service."""
        since = datetime.now(timezone.utc) - timedelta(days=days)
        
        snapshots = (
            self.db.query(PriceSnapshot)
            .filter(PriceSnapshot.service_id == service_id)
            .filter(PriceSnapshot.captured_at >= since)
            .order_by(PriceSnapshot.captured_at.asc())
            .all()
        )
        
        return [
            {
                "captured_at": s.captured_at.isoformat(),
                "provider_cost": float(s.provider_cost),
                "platform_price": float(s.platform_price),
                "markup_percentage": float(s.markup_percentage)
            }
            for s in snapshots
        ]

    def get_recent_alerts(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Fetch recent price-related admin notifications."""
        alerts = (
            self.db.query(AdminNotification)
            .filter(AdminNotification.notification_type == "price_change")
            .order_by(desc(AdminNotification.created_at))
            .limit(limit)
            .all()
        )
        
        return [
            {
                "id": a.id,
                "title": a.title,
                "message": a.message,
                "severity": a.severity,
                "is_read": a.is_read,
                "created_at": a.created_at.isoformat(),
                "metadata": a.metadata_json
            }
            for a in alerts
        ]
