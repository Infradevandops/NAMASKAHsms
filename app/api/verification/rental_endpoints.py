"""Number rental endpoints — rent dedicated numbers for long-term use."""

import asyncio
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user_id
from app.core.logging import get_logger
from app.models.transaction import Transaction
from app.models.user import User
from app.models.verification import NumberRental
from app.services.pricing_calculator import PricingCalculator
from app.services.textverified_service import TextVerifiedService

logger = get_logger(__name__)
router = APIRouter()
_tv = TextVerifiedService()


class RentalRequest(BaseModel):
    service: str
    duration_hours: float = Field(default=24.0, ge=1.0, le=720.0)
    auto_extend: bool = False


class ExtendRequest(BaseModel):
    extra_hours: float = Field(default=24.0, ge=1.0, le=720.0)


@router.post("/rentals/request", status_code=status.HTTP_201_CREATED)
async def request_rental(
    request: RentalRequest,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Rent a dedicated number for long-term use (Pro+ tier required)."""
    from app.services.tier_manager import TierManager

    tier_manager = TierManager(db)
    user_tier = tier_manager.get_user_tier(user_id)
    if not tier_manager.check_tier_hierarchy(user_tier, "pro"):
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail="Number rentals require Pro tier or higher.",
        )

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Get provider price and calculate cost
    try:
        services = await _tv.get_services_list()
        provider_price = next(
            (
                float(s.get("cost", 0))
                for s in services
                if s.get("id") == request.service
            ),
            None,
        )
    except Exception:
        provider_price = None

    if not provider_price:
        raise HTTPException(status_code=400, detail="Service not available for rental")

    pricing = PricingCalculator.calculate_rental_cost(
        db=db,
        user_id=user_id,
        provider_cost=provider_price,
        duration_hours=request.duration_hours,
        tier_name=user_tier,
    )
    total_cost = pricing["total_cost"]

    if float(user.credits or 0) < total_cost:
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail=f"Insufficient credits. Need ${total_cost:.2f}, have ${float(user.credits):.2f}",
        )

    # Create reservation via TextVerified
    reservation = await _tv.create_reservation(
        service=request.service,
        country="US",
        duration_hours=request.duration_hours,
    )

    # Deduct credits
    user.credits = type(user.credits)(float(user.credits) - total_cost)

    # Save rental record
    now = datetime.now(timezone.utc)
    rental = NumberRental(
        user_id=user_id,
        phone_number=reservation["phone_number"],
        service_name=request.service,
        duration_hours=request.duration_hours,
        cost=total_cost,
        mode="always_ready",
        status="active",
        started_at=now,
        expires_at=now + timedelta(hours=request.duration_hours),
        auto_extend=request.auto_extend,
        warning_sent=False,
    )
    db.add(rental)

    # Transaction record
    tx = Transaction(
        user_id=user_id,
        amount=-total_cost,
        type="debit",
        description=f"Number rental: {request.service} ({request.duration_hours}h)",
        status="completed",
        reference=f"rental_{reservation['id']}",
        created_at=now,
    )
    db.add(tx)
    db.commit()
    db.refresh(rental)

    return {
        "rental_id": rental.id,
        "phone_number": rental.phone_number,
        "service": rental.service_name,
        "duration_hours": rental.duration_hours,
        "cost": total_cost,
        "expires_at": rental.expires_at.isoformat(),
        "status": rental.status,
        "reservation_id": reservation["id"],
    }


@router.get("/rentals/active")
async def get_active_rentals(
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """List user's active rentals."""
    rentals = (
        db.query(NumberRental)
        .filter(NumberRental.user_id == user_id, NumberRental.status == "active")
        .order_by(NumberRental.expires_at.asc())
        .all()
    )
    now = datetime.now(timezone.utc)
    return {
        "rentals": [
            {
                "rental_id": r.id,
                "phone_number": r.phone_number,
                "service": r.service_name,
                "expires_at": r.expires_at.isoformat(),
                "minutes_remaining": max(
                    0,
                    int(
                        (
                            r.expires_at.replace(tzinfo=timezone.utc) - now
                        ).total_seconds()
                        / 60
                    ),
                ),
                "auto_extend": r.auto_extend,
                "cost": r.cost,
            }
            for r in rentals
        ]
    }


@router.get("/rentals/{rental_id}/messages")
async def get_rental_messages(
    rental_id: str,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Fetch all messages received on a rented number."""
    rental = (
        db.query(NumberRental)
        .filter(NumberRental.id == rental_id, NumberRental.user_id == user_id)
        .first()
    )
    if not rental:
        raise HTTPException(status_code=404, detail="Rental not found")

    try:
        messages = await _tv.get_reservation_messages(rental_id)
    except Exception as e:
        logger.error(f"Failed to fetch rental messages: {e}")
        messages = []

    return {
        "rental_id": rental_id,
        "phone_number": rental.phone_number,
        "messages": messages,
    }


@router.post("/rentals/{rental_id}/extend")
async def extend_rental(
    rental_id: str,
    payload: ExtendRequest,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Extend a rental by additional hours."""
    rental = (
        db.query(NumberRental)
        .filter(NumberRental.id == rental_id, NumberRental.user_id == user_id)
        .first()
    )
    if not rental:
        raise HTTPException(status_code=404, detail="Rental not found")
    if rental.status != "active":
        raise HTTPException(status_code=400, detail="Rental is not active")

    user = db.query(User).filter(User.id == user_id).first()
    extension_cost = round(
        (rental.cost / rental.duration_hours) * payload.extra_hours, 2
    )

    if float(user.credits or 0) < extension_cost:
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail=f"Insufficient credits. Need ${extension_cost:.2f}",
        )

    success = await _tv.extend_reservation(rental_id, payload.extra_hours)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to extend with provider")

    user.credits = type(user.credits)(float(user.credits) - extension_cost)
    rental.expires_at = rental.expires_at + timedelta(hours=payload.extra_hours)
    rental.duration_hours += payload.extra_hours
    rental.cost += extension_cost
    db.commit()

    return {
        "rental_id": rental_id,
        "extended_hours": payload.extra_hours,
        "cost": extension_cost,
        "new_expires_at": rental.expires_at.isoformat(),
    }


@router.post("/rentals/{rental_id}/cancel")
async def cancel_rental(
    rental_id: str,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Cancel an active rental and release the number."""
    rental = (
        db.query(NumberRental)
        .filter(NumberRental.id == rental_id, NumberRental.user_id == user_id)
        .first()
    )
    if not rental:
        raise HTTPException(status_code=404, detail="Rental not found")
    if rental.status != "active":
        raise HTTPException(status_code=400, detail="Rental is not active")

    # Attempt provider cancellation (best-effort)
    try:
        await asyncio.to_thread(_tv.client.reservations.cancel, rental_id)
    except Exception as e:
        logger.warning(f"Provider cancel failed for rental {rental_id}: {e}")

    now = datetime.now(timezone.utc)
    rental.status = "cancelled"
    rental.released_at = now

    # Partial refund: unused hours
    expires = (
        rental.expires_at.replace(tzinfo=timezone.utc)
        if rental.expires_at.tzinfo is None
        else rental.expires_at
    )
    remaining_hours = max(0, (expires - now).total_seconds() / 3600)
    refund = (
        round((rental.cost / rental.duration_hours) * remaining_hours, 2)
        if remaining_hours > 0
        else 0.0
    )

    if refund > 0:
        user = db.query(User).filter(User.id == user_id).first()
        if user:
            user.credits = type(user.credits)(float(user.credits) + refund)
            tx = Transaction(
                user_id=user_id,
                amount=refund,
                type="credit",
                description=f"Rental cancellation refund: {rental.service_name}",
                status="completed",
                reference=f"refund_rental_{rental_id}",
                created_at=now,
            )
            db.add(tx)

    db.commit()
    return {"status": "cancelled", "rental_id": rental_id, "refund": refund}
