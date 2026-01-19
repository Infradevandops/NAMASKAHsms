from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.dependencies import get_db

router = APIRouter(prefix="/waitlist", tags=["waitlist"])


@router.post("/join")
async def join_waitlist(data: WaitlistJoin, db: Session = Depends(get_db)):
    """Add email to waitlist"""
    try:
        # Check if email already exists
        existing = (
            db.query(Waitlist).filter(Waitlist.email == data.email.lower()).first()
        )
        if existing:
            return {"success": True, "message": "Email already on waitlist"}

        # Create new waitlist entry
        waitlist_entry = Waitlist(
            email=data.email.lower(), name=data.name, source=data.source
        )

        db.add(waitlist_entry)
        db.commit()

        return {"success": True, "message": "Successfully joined waitlist"}

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/list", response_model=List[WaitlistResponse])
async def get_waitlist(db: Session = Depends(get_db)):
    """Get all waitlist entries (admin only)"""
    try:
        entries = db.query(Waitlist).order_by(Waitlist.created_at.desc()).all()
        return entries
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/notify/{waitlist_id}")
async def mark_notified(waitlist_id: int, db: Session = Depends(get_db)):
    """Mark waitlist entry as notified"""
    try:
        entry = db.query(Waitlist).filter(Waitlist.id == waitlist_id).first()
        if not entry:
            raise HTTPException(status_code=404, detail="Waitlist entry not found")

        entry.is_notified = True
        db.commit()

        return {"success": True, "message": "Entry marked as notified"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
