"""Rentals SMS endpoints."""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.logging import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/rentals", tags=["Rentals"])

def get_textverified_integration():
    class Integration:
        pass
    return Integration()

integration = get_textverified_integration()

@router.get("/status")
async def get_status(db: Session = Depends(get_db)):
    """Get rentals service status."""
    return {"status": "operational"}
