"""SMS Inbox endpoints for real SMS message management."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime

from app.core.database import get_db
from app.core.dependencies import get_current_user_id
from app.services.textverified_integration import get_textverified_integration
from app.models.sms_message import SMSMessage
from app.models.rental import Rental
from app.core.logging import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/api/sms", tags=["sms"])
integration = get_textverified_integration()


@router.get("/inbox")
async def get_inbox(
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
    limit: int = 50,
    offset: int = 0,
):
    """Get user's SMS inbox."""
    try:
        messages = db.query(SMSMessage).filter(
            SMSMessage.user_id == user_id
        ).order_by(
            SMSMessage.received_at.desc()
        ).offset(offset).limit(limit).all()

        unread_count = db.query(SMSMessage).filter(
            SMSMessage.user_id == user_id,
            SMSMessage.is_read == False
        ).count()

        return {
            "success": True,
            "messages": [
                {
                    "id": m.id,
                    "from": m.from_number,
                    "text": m.text,
                    "received_at": m.received_at.isoformat(),
                    "is_read": m.is_read,
                    "rental_id": m.rental_id,
                }
                for m in messages
            ],
            "total": len(messages),
            "unread_count": unread_count,
        }

    except Exception as e:
        logger.error(f"Get inbox error: {e}")
        raise HTTPException(status_code=500, detail="Failed to get inbox")


@router.post("/inbox/sync")
async def sync_inbox(
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Sync SMS messages from TextVerified API."""
    try:
        rentals = db.query(Rental).filter(
            Rental.user_id == user_id,
            Rental.status == "active"
        ).all()

        synced_count = 0
        for rental in rentals:
            try:
                messages = await integration.client.get_sms_messages(rental.external_id)

                for msg in messages:
                    existing = db.query(SMSMessage).filter(
                        SMSMessage.external_id == msg.get("id")
                    ).first()

                    if not existing:
                        sms = SMSMessage(
                            user_id=user_id,
                            rental_id=rental.id,
                            from_number=msg.get("from"),
                            text=msg.get("text"),
                            external_id=msg.get("id"),
                            received_at=datetime.fromisoformat(
                                msg.get("received_at", datetime.utcnow().isoformat()).replace("Z", "+00:00")
                            ),
                            is_read=False,
                        )
                        db.add(sms)
                        synced_count += 1

            except Exception as e:
                logger.error(f"Failed to sync messages for rental {rental.id}: {e}")
                continue

        db.commit()

        return {
            "success": True,
            "synced_count": synced_count,
            "message": f"Synced {synced_count} new messages",
        }

    except Exception as e:
        logger.error(f"Sync inbox error: {e}")
        raise HTTPException(status_code=500, detail="Failed to sync inbox")


@router.post("/{message_id}/mark-read")
async def mark_message_read(
    message_id: str,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Mark SMS message as read."""
    try:
        message = db.query(SMSMessage).filter(
            SMSMessage.id == message_id,
            SMSMessage.user_id == user_id
        ).first()

        if not message:
            raise HTTPException(status_code=404, detail="Message not found")

        message.is_read = True
        db.commit()

        return {
            "success": True,
            "message": "Message marked as read",
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Mark read error: {e}")
        raise HTTPException(status_code=500, detail="Failed to mark message as read")


@router.get("/inbox/unread-count")
async def get_unread_count(
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Get unread message count."""
    try:
        count = db.query(SMSMessage).filter(
            SMSMessage.user_id == user_id,
            SMSMessage.is_read == False
        ).count()

        return {
            "success": True,
            "unread_count": count,
        }

    except Exception as e:
        logger.error(f"Get unread count error: {e}")
        raise HTTPException(status_code=500, detail="Failed to get unread count")


@router.delete("/{message_id}")
async def delete_message(
    message_id: str,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Delete SMS message."""
    try:
        message = db.query(SMSMessage).filter(
            SMSMessage.id == message_id,
            SMSMessage.user_id == user_id
        ).first()

        if not message:
            raise HTTPException(status_code=404, detail="Message not found")

        db.delete(message)
        db.commit()

        return {
            "success": True,
            "message": "Message deleted",
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Delete message error: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete message")
