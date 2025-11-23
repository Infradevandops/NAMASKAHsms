"""SMS forwarding configuration endpoints."""
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.core.database import get_db

logger = get_logger(__name__)
router = APIRouter(prefix="/api/forwarding", tags=["forwarding"])


@router.post("/setup")
async def setup_forwarding(
    request: Request,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Setup SMS forwarding."""
    try:
        data = await request.json()
        rental_id = data.get("rental_id")
        phone_number = data.get("phone_number")
        email = data.get("email")
        telegram_id = data.get("telegram_id")

        rental = db.query(Rental).filter(
            Rental.id == rental_id, Rental.user_id == user_id
        ).first()

        if not rental:
            raise HTTPException(status_code=404, detail="Rental not found")

        # Check if forwarding already exists
        forwarding = db.query(SMSForwarding).filter(
            SMSForwarding.rental_id == rental_id
        ).first()

        if not forwarding:
            forwarding = SMSForwarding(user_id=user_id, rental_id=rental_id)

        # Update forwarding settings
        if phone_number:
            forwarding.phone_number = phone_number
            forwarding.phone_enabled = True
        if email:
            forwarding.email = email
            forwarding.email_enabled = True
        if telegram_id:
            forwarding.telegram_id = telegram_id
            forwarding.telegram_enabled = True

        db.add(forwarding)
        db.commit()

        return {
            "success": True,
            "id": forwarding.id,
            "message": "Forwarding configured successfully",
        }

    except HTTPException:
        pass
    except Exception as e:
        logger.error(f"Setup forwarding error: {e}")
        raise HTTPException(status_code=500, detail="Failed to setup forwarding")


@router.get("/{rental_id}")
async def get_forwarding_settings(
    rental_id: str,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Get forwarding settings for rental."""
    try:
        rental = db.query(Rental).filter(
            Rental.id == rental_id, Rental.user_id == user_id
        ).first()

        if not rental:
            raise HTTPException(status_code=404, detail="Rental not found")

        forwarding = db.query(SMSForwarding).filter(
            SMSForwarding.rental_id == rental_id
        ).first()

        if not forwarding:
            return {
                "success": True,
                "forwarding": None,
                "message": "No forwarding configured",
            }

        return {
            "success": True,
            "forwarding": {
                "id": forwarding.id,
                "phone_number": forwarding.phone_number if forwarding.phone_enabled else None,
                "email": forwarding.email if forwarding.email_enabled else None,
                "telegram_id": forwarding.telegram_id if forwarding.telegram_enabled else None,
                "phone_enabled": forwarding.phone_enabled,
                "email_enabled": forwarding.email_enabled,
                "telegram_enabled": forwarding.telegram_enabled,
            },
        }

    except HTTPException:
        pass
    except Exception as e:
        logger.error(f"Get forwarding settings error: {e}")
        raise HTTPException(status_code=500, detail="Failed to get forwarding settings")


@router.post("/{rental_id}/disable")
async def disable_forwarding(
    rental_id: str,
    request: Request,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Disable forwarding for rental."""
    try:
        data = await request.json()
        forwarding_type = data.get("type")  # phone, email, telegram

        rental = db.query(Rental).filter(
            Rental.id == rental_id, Rental.user_id == user_id
        ).first()

        if not rental:
            raise HTTPException(status_code=404, detail="Rental not found")

        forwarding = db.query(SMSForwarding).filter(
            SMSForwarding.rental_id == rental_id
        ).first()

        if not forwarding:
            raise HTTPException(status_code=404, detail="Forwarding not configured")

        if forwarding_type == "phone":
            forwarding.phone_enabled = False
        elif forwarding_type == "email":
            forwarding.email_enabled = False
        elif forwarding_type == "telegram":
            forwarding.telegram_enabled = False

        db.commit()

        return {
            "success": True,
            "message": f"{forwarding_type} forwarding disabled",
        }

    except HTTPException:
        pass
    except Exception as e:
        logger.error(f"Disable forwarding error: {e}")
        raise HTTPException(status_code=500, detail="Failed to disable forwarding")
