"""Number blacklist API endpoints."""

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field, field_validator
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user_id
from app.core.logging import get_logger
from app.models.blacklist import NumberBlacklist

logger = get_logger(__name__)


class BlacklistCreate(BaseModel):
    phone_number: str = Field(..., description="Phone number to blacklist")
    service_name: str = Field(default="all", description="Service name")
    country: str = Field(default=None, description="Country code")
    reason: str = Field(default="manual_block", description="Reason for blacklisting")
    days: int = Field(default=30, description="Number of days to blacklist")

    @field_validator("phone_number")
    @classmethod
    def validate_phone(cls, v):
        if not v.startswith("+") or len(v) < 7:
            raise ValueError("Phone number must start with + and be at least 7 digits")
        return v


router = APIRouter(prefix="/blacklist", tags=["Blacklist"])


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
    country = request.country
    reason = request.reason
    days = request.days
    try:
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
        blacklist_entry = NumberBlacklist.create_blacklist_entry(
            user_id=user_id,
            phone_number=phone_number,
            service_name=service_name,
            country=country,
            reason=reason,
            is_manual=True,
            days=days,
        )

        db.add(blacklist_entry)
        db.commit()

        return {
            "success": True,
            "message": f"Number {phone_number} blacklisted for {days} days",
            "expires_at": blacklist_entry.expires_at.isoformat(),
        }

    except Exception as e:
        logger.error(f"Failed to add to blacklist: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("")
async def get_blacklist(
    service_name: str = None,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Get user's blacklisted numbers."""
    try:
        query = db.query(NumberBlacklist).filter(NumberBlacklist.user_id == user_id)

        if service_name:
            query = query.filter(NumberBlacklist.service_name == service_name)

        blacklist = query.all()

        # Filter out expired entries
        active_blacklist = [
            {
                "id": entry.id,
                "phone_number": entry.phone_number,
                "service_name": entry.service_name,
                "country": entry.country,
                "reason": entry.reason,
                "is_manual": entry.is_manual,
                "created_at": entry.created_at.isoformat(),
                "expires_at": entry.expires_at.isoformat(),
                "is_expired": entry.is_expired,
            }
            for entry in blacklist
            if not entry.is_expired
        ]

        return {
            "success": True,
            "blacklist": active_blacklist,
            "total": len(active_blacklist),
        }

    except Exception as e:
        logger.error(f"Failed to get blacklist: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{blacklist_id}")
async def remove_from_blacklist(
    blacklist_id: str,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Remove number from blacklist."""
    try:
        entry = (
            db.query(NumberBlacklist)
            .filter(
                NumberBlacklist.id == blacklist_id, NumberBlacklist.user_id == user_id
            )
            .first()
        )

        if not entry:
            raise HTTPException(status_code=404, detail="Blacklist entry not found")

        db.delete(entry)
        db.commit()

        return {
            "success": True,
            "message": f"Number {entry.phone_number} removed from blacklist",
        }

    except HTTPException:
        pass
    except Exception as e:
        logger.error(f"Failed to remove from blacklist: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/check")
async def check_blacklist(
    phone_number: str,
    service_name: str,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Check if number is blacklisted."""
    try:
        entry = (
            db.query(NumberBlacklist)
            .filter(
                NumberBlacklist.user_id == user_id,
                NumberBlacklist.phone_number == phone_number,
                NumberBlacklist.service_name == service_name,
            )
            .first()
        )

        if not entry or entry.is_expired:
            return {"blacklisted": False, "message": "Number is not blacklisted"}

        return {
            "blacklisted": True,
            "reason": entry.reason,
            "expires_at": entry.expires_at.isoformat(),
            "message": f"Number is blacklisted until {entry.expires_at.strftime('%Y-%m-%d')}",
        }

    except Exception as e:
        logger.error(f"Failed to check blacklist: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/cleanup")
async def cleanup_expired(
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Remove expired blacklist entries."""
    try:
        expired = (
            db.query(NumberBlacklist)
            .filter(
                NumberBlacklist.user_id == user_id,
                NumberBlacklist.expires_at < datetime.now(timezone.utc),
            )
            .all()
        )

        count = len(expired)

        for entry in expired:
            db.delete(entry)

        db.commit()

        return {"success": True, "message": f"Removed {count} expired entries"}

    except Exception as e:
        logger.error(f"Failed to cleanup blacklist: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
