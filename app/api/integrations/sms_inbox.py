"""SMS Inbox endpoints."""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.logging import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/sms", tags=["SMS"])

def get_textverified_integration():
    class Integration:
        pass
    return Integration()

integration = get_textverified_integration()

@router.get("/inbox")
async def get_inbox(db: Session = Depends(get_db)):
    """Get SMS inbox."""
    return {"messages": []}
