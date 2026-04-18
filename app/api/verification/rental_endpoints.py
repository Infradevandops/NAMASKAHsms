"""Rental verification endpoints (V6.0 Institutional Grade).

Full CRUD + message retrieval + expiry status:
  POST  /rentals/request        → purchase a new rental
  GET   /rentals/active         → list active rentals
  GET   /rentals/{id}           → get single rental detail
  GET   /rentals/{id}/messages  → fetch all SMS received on rental
  GET   /rentals/{id}/expiry    → real-time expiry status
  POST  /rentals/{id}/cancel    → cancel with prorated refund
  POST  /rentals/{id}/extend    → extend with balance deduction
"""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user_id
from app.schemas.verification import VerificationRequest
from app.services.rental_service import RentalService

router = APIRouter(prefix="/rentals", tags=["Rentals"])


# ── Request Schemas ───────────────────────────────────────────────────────────


class RentalExtendRequest(BaseModel):
    extra_hours: float = Field(..., gt=0, le=720, description="Hours to add (max 30 days)")


# ── Helpers ───────────────────────────────────────────────────────────────────


def _format_rental(r) -> dict:
    """Serialize a NumberRental ORM object to a safe dict."""
    return {
        "id": r.id,
        "phone_number": r.phone_number,
        "service": r.service_name,
        "duration_hours": r.duration_hours,
        "cost": r.cost,
        "status": r.status,
        "mode": r.mode,
        "started_at": r.started_at.isoformat() if r.started_at else None,
        "expires_at": r.expires_at.isoformat() if r.expires_at else None,
        "auto_extend": r.auto_extend,
        "warning_sent": r.warning_sent,
    }


# ── Endpoints ─────────────────────────────────────────────────────────────────


@router.post("/request", status_code=status.HTTP_201_CREATED, summary="Purchase a number rental")
async def request_rental(
    request: VerificationRequest,
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """Purchase a new long-term number rental.

    The provider will reserve a dedicated phone number for `duration_hours`.
    Credits are atomically debited; a prorated refund is issued on cancellation.
    """
    svc = RentalService(db)
    try:
        duration = getattr(request, "duration_hours", 24.0) or 24.0
        result = await svc.purchase_rental(
            user_id=user_id,
            service=request.service,
            country=request.country or "US",
            duration_hours=duration,
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        import logging
        logging.getLogger(__name__).error(f"Rental request failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Rental service temporarily unavailable")


@router.get("/active", summary="List active rentals")
async def get_active_rentals(
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """Return all active rentals for the authenticated user, sorted by expiry."""
    svc = RentalService(db)
    rentals = await svc.get_active_rentals(user_id)
    return {"rentals": [_format_rental(r) for r in rentals], "total": len(rentals)}


@router.get("/{rental_id}", summary="Get a single rental")
async def get_rental(
    rental_id: int,
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """Get the full details for a specific rental."""
    svc = RentalService(db)
    rental = await svc.get_rental(rental_id, user_id)
    if not rental:
        raise HTTPException(status_code=404, detail=f"Rental {rental_id} not found")
    return _format_rental(rental)


@router.get("/{rental_id}/messages", summary="Fetch SMS received on a rental number")
async def get_rental_messages(
    rental_id: int,
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """Fetch all SMS messages received on a rented number from TextVerified."""
    svc = RentalService(db)
    messages = await svc.check_rental_messages(rental_id, user_id=user_id)
    return {"messages": messages, "count": len(messages)}


@router.get("/{rental_id}/expiry", summary="Real-time expiry status")
async def get_rental_expiry(
    rental_id: int,
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """Returns the real-time expiry status of a rental, sourced live from TextVerified."""
    svc = RentalService(db)
    try:
        return await svc.check_expiry_status(rental_id, user_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{rental_id}/cancel", summary="Cancel rental with prorated refund")
async def cancel_rental(
    rental_id: int,
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """Cancel an active rental. A prorated refund (unused time) is issued immediately."""
    svc = RentalService(db)
    try:
        result = await svc.cancel_rental(rental_id, user_id)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        import logging
        logging.getLogger(__name__).error(f"Rental cancel failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to cancel rental")


@router.post("/{rental_id}/extend", summary="Extend rental duration")
async def extend_rental(
    rental_id: int,
    body: RentalExtendRequest,
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """Extend an active rental by `extra_hours`. Credits are debited at the current tier rate."""
    svc = RentalService(db)
    try:
        result = await svc.extend_rental(rental_id, user_id, body.extra_hours)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        import logging
        logging.getLogger(__name__).error(f"Rental extend failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to extend rental")
