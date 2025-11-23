"""Real TextVerified rental endpoints."""
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from datetime import datetime

from app.core.database import get_db

logger = get_logger(__name__)
router = APIRouter(prefix="/api/rentals", tags=["rentals"])
integration = get_textverified_integration()


@router.post("/create")
async def create_rental(
    request: Request,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Create real phone number rental with TextVerified API."""
    try:
        data = await request.json()
        service = data.get("service")
        duration_days = data.get("duration_days", 30)
        renewable = data.get("renewable", False)

        if not service:
            raise HTTPException(status_code=400, detail="Service required")

        if duration_days < 1 or duration_days > 365:
            raise HTTPException(status_code=400, detail="Duration must be 1-365 days")

        # Get user and check balance
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        # Create rental with real API
        result = await integration.create_rental(
            service=service, duration_days=duration_days, renewable=renewable
        )

        cost = result.get("cost", 0.0)
        if user.credits < cost:
            raise HTTPException(status_code=400, detail="Insufficient credits")

        # Deduct cost from user balance
        user.credits -= cost
        db.commit()

        # Store rental in database
        expires_at = result.get("expires_at")
        if isinstance(expires_at, str):
            expires_at = datetime.fromisoformat(expires_at.replace("Z", "+00:00"))

        rental = Rental(
            user_id=user_id,
            service_name=service,
            phone_number=result["phone_number"],
            status="active",
            cost=cost,
            external_id=result["id"],
            renewable=renewable,
            expires_at=expires_at,
        )
        db.add(rental)
        db.commit()

        return {
            "success": True,
            "id": rental.id,
            "external_id": result["id"],
            "phone_number": result["phone_number"],
            "service": service,
            "status": "active",
            "cost": cost,
            "renewable": renewable,
            "expires_at": rental.expires_at.isoformat(),
            "created_at": rental.created_at.isoformat(),
        }

    except HTTPException:
        pass
    except Exception as e:
        logger.error(f"Rental creation error: {e}")
        raise HTTPException(status_code=500, detail="Failed to create rental")


@router.get("/active")
async def get_active_rentals(user_id: str = Depends(get_current_user_id), db: Session = Depends(get_db)):
    """Get user's active rentals."""
    try:
        rentals = db.query(Rental).filter(
            Rental.user_id == user_id, Rental.status == "active"
        ).all()

        return {
            "success": True,
            "rentals": [
                {
                    "id": r.id,
                    "phone_number": r.phone_number,
                    "service": r.service_name,
                    "status": r.status,
                    "renewable": r.renewable,
                    "expires_at": r.expires_at.isoformat(),
                    "created_at": r.created_at.isoformat(),
                }
                for r in rentals
            ],
            "total": len(rentals),
        }

    except Exception as e:
        logger.error(f"Get rentals error: {e}")
        raise HTTPException(status_code=500, detail="Failed to get rentals")


@router.post("/{rental_id}/extend")
async def extend_rental(
    rental_id: str,
    request: Request,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Extend rental duration."""
    try:
        data = await request.json()
        duration_days = data.get("duration_days", 30)

        if duration_days < 1 or duration_days > 365:
            raise HTTPException(status_code=400, detail="Duration must be 1-365 days")

        rental = db.query(Rental).filter(
            Rental.id == rental_id, Rental.user_id == user_id
        ).first()

        if not rental:
            raise HTTPException(status_code=404, detail="Rental not found")

        # Get user and check balance
        user = db.query(User).filter(User.id == user_id).first()

        # Extend with real API
        result = await integration.extend_rental(rental.external_id, duration_days)

        cost = result.get("cost", 0.0)
        if user.credits < cost:
            raise HTTPException(status_code=400, detail="Insufficient credits")

        # Deduct cost
        user.credits -= cost
        expires_at = result.get("expires_at")
        if isinstance(expires_at, str):
            expires_at = datetime.fromisoformat(expires_at.replace("Z", "+00:00"))
        rental.expires_at = expires_at
        db.commit()

        return {
            "success": True,
            "id": rental.id,
            "expires_at": rental.expires_at.isoformat(),
            "cost": cost,
            "message": "Rental extended successfully",
        }

    except HTTPException:
        pass
    except Exception as e:
        logger.error(f"Extend rental error: {e}")
        raise HTTPException(status_code=500, detail="Failed to extend rental")


@router.get("/{rental_id}/details")
async def get_rental_details(
    rental_id: str,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Get rental details."""
    try:
        rental = db.query(Rental).filter(
            Rental.id == rental_id, Rental.user_id == user_id
        ).first()

        if not rental:
            raise HTTPException(status_code=404, detail="Rental not found")

        return {
            "success": True,
            "id": rental.id,
            "phone_number": rental.phone_number,
            "service": rental.service_name,
            "status": rental.status,
            "renewable": rental.renewable,
            "expires_at": rental.expires_at.isoformat(),
            "created_at": rental.created_at.isoformat(),
            "cost": rental.cost,
        }

    except HTTPException:
        pass
    except Exception as e:
        logger.error(f"Get rental details error: {e}")
        raise HTTPException(status_code=500, detail="Failed to get rental details")
