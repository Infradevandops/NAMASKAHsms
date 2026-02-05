"""Phone number blacklist API endpoints."""

from datetime import datetime
from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.dependencies import get_current_user_id
from app.core.logging import get_logger
from app.models.blacklist import NumberBlacklist
from app.schemas.validators import BlacklistCreate, BlacklistResponse

logger = get_logger(__name__)
router = APIRouter(prefix="/api/blacklist", tags=["Number Blacklist"])


@router.get("", response_model=List[BlacklistResponse])
async def get_blacklist(
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Get user's blacklisted numbers."""
    blacklisted_numbers = (
        db.query(NumberBlacklist)
        .filter(NumberBlacklist.user_id == user_id)
        .order_by(NumberBlacklist.created_at.desc())
        .all()
    )

    return [
        BlacklistResponse(
            id=entry.id,
            phone_number=entry.phone_number,
            service_name=entry.service_name,
            reason=entry.reason,
            created_at=entry.created_at,
            expires_at=entry.expires_at,
            is_expired=entry.is_expired,
        )
        for entry in blacklisted_numbers
    ]


@router.post("")
@router.post("/add")
async def add_to_blacklist(
    request: BlacklistCreate,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Manually add number to blacklist."""
    phone_number = request.phone_number
    service_name = request.service_name

    # Check if already blacklisted
    existing = (
        db.query(NumberBlacklist)
        .filter(
            NumberBlacklist.user_id == user_id,
            NumberBlacklist.phone_number == phone_number,
            NumberBlacklist.service_name == service_name,
        )
        .first()
    )

    if existing and not existing.is_expired:
        return {
            "success": False,
            "message": "Number already blacklisted",
            "expires_at": existing.expires_at.isoformat(),
        }

    # Create blacklist entry
    blacklist_entry = NumberBlacklist(
        user_id=user_id,
        phone_number=phone_number,
        service_name=service_name,
        reason=request.reason or "Manual blacklist",
        created_at=datetime.utcnow(),
        expires_at=datetime.utcnow().replace(year=datetime.utcnow().year + 1),  # 1 year
    )

    db.add(blacklist_entry)
    db.commit()
    db.refresh(blacklist_entry)

    logger.info(f"Number {phone_number} blacklisted by user {user_id} for service {service_name}")

    return {
        "success": True,
        "message": "Number added to blacklist",
        "id": blacklist_entry.id,
        "expires_at": blacklist_entry.expires_at.isoformat(),
    }


@router.delete("/{blacklist_id}")
async def remove_from_blacklist(
    blacklist_id: str,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Remove number from blacklist."""
    blacklist_entry = (
        db.query(NumberBlacklist)
        .filter(
            NumberBlacklist.id == blacklist_id,
            NumberBlacklist.user_id == user_id,
        )
        .first()
    )

    if not blacklist_entry:
        raise HTTPException(status_code=404, detail="Blacklist entry not found")

    db.delete(blacklist_entry)
    db.commit()

    logger.info(f"Blacklist entry {blacklist_id} removed by user {user_id}")

    return {"success": True, "message": "Number removed from blacklist"}


@router.post("/check")
async def check_blacklist(
    phone_number: str,
    service_name: str,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Check if a number is blacklisted."""
    blacklist_entry = (
        db.query(NumberBlacklist)
        .filter(
            NumberBlacklist.user_id == user_id,
            NumberBlacklist.phone_number == phone_number,
            NumberBlacklist.service_name == service_name,
        )
        .first()
    )

    is_blacklisted = blacklist_entry is not None and not blacklist_entry.is_expired

    return {
        "phone_number": phone_number,
        "service_name": service_name,
        "is_blacklisted": is_blacklisted,
        "reason": blacklist_entry.reason if blacklist_entry else None,
        "expires_at": blacklist_entry.expires_at.isoformat() if blacklist_entry else None,
    }


@router.post("/cleanup")
async def cleanup_expired(
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Remove expired blacklist entries."""
    expired_entries = (
        db.query(NumberBlacklist)
        .filter(
            NumberBlacklist.user_id == user_id,
            NumberBlacklist.expires_at < datetime.utcnow(),
        )
        .all()
    )

    count = len(expired_entries)
    for entry in expired_entries:
        db.delete(entry)

    db.commit()

    logger.info(f"Cleaned up {count} expired blacklist entries for user {user_id}")

    return {"success": True, "message": f"Removed {count} expired entries"}
