"""Stock watch endpoints — users subscribe to back-in-stock notifications."""

import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user_id
from app.models.stock_watch import StockWatch

router = APIRouter(prefix="/notifications", tags=["Notifications"])


class StockWatchRequest(BaseModel):
    service_name: str
    capability: str = "sms"


@router.post("/stock-watch", status_code=201)
async def create_stock_watch(
    body: StockWatchRequest,
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """Subscribe to back-in-stock notification for a service."""
    existing = (
        db.query(StockWatch)
        .filter(
            StockWatch.user_id == user_id,
            StockWatch.service_name == body.service_name,
            StockWatch.capability == body.capability,
        )
        .first()
    )
    if existing:
        return {"message": "Already watching", "id": str(existing.id)}

    watch = StockWatch(
        id=str(uuid.uuid4()),
        user_id=user_id,
        service_name=body.service_name,
        capability=body.capability,
        created_at=datetime.now(timezone.utc),
    )
    db.add(watch)
    db.commit()
    return {"message": "Watch created", "id": str(watch.id)}


@router.delete("/stock-watch/{service_name}", status_code=204)
async def delete_stock_watch(
    service_name: str,
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """Cancel a stock watch."""
    watch = (
        db.query(StockWatch)
        .filter(StockWatch.user_id == user_id, StockWatch.service_name == service_name)
        .first()
    )
    if watch:
        db.delete(watch)
        db.commit()


@router.get("/stock-watches")
async def list_stock_watches(
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """List active stock watches for the current user."""
    watches = (
        db.query(StockWatch)
        .filter(StockWatch.user_id == user_id, StockWatch.notified_at.is_(None))
        .all()
    )
    return [
        {
            "id": str(w.id),
            "service_name": w.service_name,
            "capability": w.capability,
            "created_at": w.created_at.isoformat(),
        }
        for w in watches
    ]
