"""Billing cycle management endpoints."""
from app.core.dependencies import get_current_user_id
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db

logger = get_logger(__name__)
router = APIRouter(prefix="/api/billing-cycles", tags=["billing-cycles"])
client = get_textverified_client()


@router.get("/list")
async def list_billing_cycles(
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Get billing cycles for user's rentals."""
    try:
        rentals = db.query(Rental).filter(
            Rental.user_id == user_id, Rental.renewable
        ).all()

        headers = await client.auth_service.get_headers()
        import httpx

        cycles = []
        async with httpx.AsyncClient() as http_client:
            for rental in rentals:
                try:
                    response = await http_client.get(
                        f"{client.BASE_URL}/api/pub/v2/billing-cycles",
                        headers=headers,
                        params={"reservationId": rental.external_id},
                        timeout=10.0,
                    )
                    response.raise_for_status()
                    data = response.json()

                    for cycle in data.get("billingCycles", []):
                        cycles.append(
                            {
                                "id": cycle.get("id"),
                                "rental_id": rental.id,
                                "status": cycle.get("status"),
                                "next_renewal": cycle.get("nextRenewalDate"),
                                "cost": float(cycle.get("cost", 0)),
                            }
                        )
                except Exception as e:
                    logger.error(f"Failed to get billing cycles for rental {rental.id}: {e}")
                    continue

        return {
            "success": True,
            "billing_cycles": cycles,
            "total": len(cycles),
        }

    except Exception as e:
        logger.error(f"List billing cycles error: {e}")
        raise HTTPException(status_code=500, detail="Failed to list billing cycles")


@router.post("/{cycle_id}/renew")
async def renew_billing_cycle(
    cycle_id: str,
    user_id: str = Depends(get_current_user_id),
):
    """Renew billing cycle."""
    try:
        headers = await client.auth_service.get_headers()

        async with httpx.AsyncClient() as http_client:
            response = await http_client.post(
                f"{client.BASE_URL}/api/pub/v2/billing-cycles/{cycle_id}/renew",
                headers=headers,
                timeout=10.0,
            )
            response.raise_for_status()
            data = response.json()

            return {
                "success": True,
                "id": data.get("id"),
                "status": data.get("status"),
                "next_renewal": data.get("nextRenewalDate"),
                "message": "Billing cycle renewed successfully",
            }

    except Exception as e:
        logger.error(f"Renew billing cycle error: {e}")
        raise HTTPException(status_code=500, detail="Failed to renew billing cycle")


@router.get("/{cycle_id}/invoices")
async def get_cycle_invoices(
    cycle_id: str,
    user_id: str = Depends(get_current_user_id),
):
    """Get invoices for billing cycle."""
    try:
        headers = await client.auth_service.get_headers()

        async with httpx.AsyncClient() as http_client:
            response = await http_client.get(
                f"{client.BASE_URL}/api/pub/v2/billing-cycles/{cycle_id}/invoices",
                headers=headers,
                timeout=10.0,
            )
            response.raise_for_status()
            data = response.json()

            invoices = []
            for invoice in data.get("invoices", []):
                invoices.append(
                    {
                        "id": invoice.get("id"),
                        "amount": float(invoice.get("amount", 0)),
                        "date": invoice.get("date"),
                        "status": invoice.get("status"),
                    }
                )

            return {
                "success": True,
                "invoices": invoices,
                "total": len(invoices),
            }

    except Exception as e:
        logger.error(f"Get cycle invoices error: {e}")
        raise HTTPException(status_code=500, detail="Failed to get invoices")
