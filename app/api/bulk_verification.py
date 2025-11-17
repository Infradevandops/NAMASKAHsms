"""Bulk verification API endpoints."""

import asyncio
from datetime import datetime, timezone
from decimal import Decimal
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user_id
from app.core.logging import get_logger
from app.models.user import User
from app.models.verification import Verification
from app.services.textverified_service import TextVerifiedService

logger = get_logger(__name__)

router = APIRouter(prefix="/verify/bulk", tags=["Bulk Verification"])


class BulkVerificationCreate:
    """Schema for bulk verification creation."""

    def __init__(
        self,
        service_name: str,
        country: str,
        quantity: int,
        capability: str = "sms",
        operator: str = "any",
        pricing_tier: str = "standard",
    ):
        self.service_name = service_name
        self.country = country
        self.quantity = quantity
        self.capability = capability
        self.operator = operator
        self.pricing_tier = pricing_tier


class BulkVerificationResponse:
    """Schema for bulk verification response."""

    def __init__(
        self,
        bulk_id: str,
        service_name: str,
        country: str,
        quantity: int,
        total_cost: float,
        discount_amount: float,
        discount_percentage: float,
        verifications: List[dict],
        successful: int,
        failed: int,
        status: str,
    ):
        self.bulk_id = bulk_id
        self.service_name = service_name
        self.country = country
        self.quantity = quantity
        self.total_cost = total_cost
        self.discount_amount = discount_amount
        self.discount_percentage = discount_percentage
        self.verifications = verifications
        self.successful = successful
        self.failed = failed
        self.status = status


def calculate_bulk_discount(quantity: int, base_price: float) -> tuple[float, float, float]:
    """
    Calculate bulk discount based on quantity.

    Discount tiers:
    - 2-4 numbers: 5% discount
    - 5-9 numbers: 15% discount
    - 10-19 numbers: 25% discount
    - 20+ numbers: 30% discount
    """

    if quantity >= 20:
        discount_pct = 0.30
    elif quantity >= 10:
        discount_pct = 0.25
    elif quantity >= 5:
        discount_pct = 0.15
    elif quantity >= 2:
        discount_pct = 0.05
    else:
        discount_pct = 0.0

    total_before_discount = base_price * quantity
    discount_amount = total_before_discount * discount_pct
    total_after_discount = total_before_discount - discount_amount

    return total_after_discount, discount_amount, discount_pct


@router.post("/create")
async def create_bulk_verification(
    service_name: str,
    country: str,
    quantity: int,
    capability: str = "sms",
    operator: str = "any",
    pricing_tier: str = "standard",
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """
    Create bulk verification purchase (2-50 numbers).

    Bulk discounts:
    - 2-4 numbers: 5% off
    - 5-9 numbers: 15% off
    - 10-19 numbers: 25% off
    - 20+ numbers: 30% off
    """

    try:
        # Validate quantity
        if quantity < 2:
            raise HTTPException(
                status_code=400,
                detail="Bulk purchase requires minimum 2 numbers",
            )
        if quantity > 50:
            raise HTTPException(
                status_code=400,
                detail="Bulk purchase limited to maximum 50 numbers",
            )

        # Get user
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        # Initialize TextVerified service (primary SMS provider)
        textverified = TextVerifiedService()

        # For TextVerified, we don't have service-level pricing, use a fixed cost
        # In a real implementation, you would query the provider API for current pricing
        try:
            # TextVerified doesn't have a service availability endpoint like 5SIM
            # Assuming the service is available for the given country
            base_cost = 0.50  # Default fixed cost per verification
        except Exception as e:
            logger.error(f"Failed to get pricing: {str(e)}")
            base_cost = 0.50  # Fallback pricing

        # Calculate final cost with tier pricing
        final_base_cost = base_cost  # TextVerified doesn't have tier-based pricing

        # Calculate bulk discount
        total_cost, discount_amount, discount_pct = calculate_bulk_discount(
            quantity, final_base_cost
        )

        # Check user credits
        if user.credits < total_cost:
            raise HTTPException(
                status_code=402,
                detail=f"Insufficient credits. Need ${total_cost:.2f}, have ${user.credits:.2f}",
            )

        # Deduct credits upfront
        user.credits -= Decimal(str(total_cost))
        db.commit()

        # Generate bulk ID
        bulk_id = f"bulk_{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}_{user_id[:8]}"

        # Purchase numbers in parallel (with concurrency limit)
        verifications = []
        successful = 0
        failed = 0

        # Create tasks for parallel execution
        async def purchase_single():
            try:
                # TextVerified SMS purchase - simplified API
                # Note: TextVerified doesn't support voice calls like 5SIM did
                phone = await textverified.get_phone_number(country)

                # Create verification record
                verification = Verification(
                    user_id=user_id,
                    service_name=service_name,
                    capability="sms",  # TextVerified only supports SMS
                    status="pending",
                    cost=Decimal(str(final_base_cost * (1 - discount_pct))),
                    phone_number=phone,
                    country=country,
                    verification_code="pending",  # Will be updated when OTP arrives
                )

                if hasattr(verification, "provider"):
                    verification.provider = "textverified"
                if hasattr(verification, "pricing_tier"):
                    verification.pricing_tier = "standard"  # TextVerified doesn't have tiers
                if hasattr(verification, "bulk_id"):
                    verification.bulk_id = bulk_id

                db.add(verification)
                db.commit()
                db.refresh(verification)

                return {
                    "success": True,
                    "verification_id": verification.id,
                    "phone_number": verification.phone_number,
                }

            except Exception as e:
                logger.error(f"Failed to purchase number: {str(e)}")
                return {"success": False, "error": str(e)}

        # Execute purchases with concurrency limit (5 at a time)
        semaphore = asyncio.Semaphore(5)

        async def purchase_with_limit():
            async with semaphore:
                return await purchase_single()

        # Create all tasks
        tasks = [purchase_with_limit() for _ in range(quantity)]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Process results
        for result in results:
            if isinstance(result, Exception):
                failed += 1
                verifications.append({"success": False, "error": str(result)})
            elif result.get("success"):
                successful += 1
                verifications.append(result)
            else:
                failed += 1
                verifications.append(result)

        # Refund for failed purchases
        if failed > 0:
            refund_amount = (final_base_cost * (1 - discount_pct)) * failed
            user.credits += Decimal(str(refund_amount))
            db.commit()
            logger.info(f"Refunded ${refund_amount:.2f} for {failed} failed purchases")

        # Determine overall status
        if successful == quantity:
            bulk_status = "completed"
        elif successful > 0:
            bulk_status = "partial"
        else:
            bulk_status = "failed"

        logger.info(
            f"Bulk purchase {bulk_id}: {successful}/{quantity} successful, "
            f"${total_cost:.2f} total (${discount_amount:.2f} discount)"
        )

        return {
            "bulk_id": bulk_id,
            "service_name": service_name,
            "country": country,
            "quantity": quantity,
            "total_cost": round(total_cost, 2),
            "discount_amount": round(discount_amount, 2),
            "discount_percentage": round(discount_pct * 100, 1),
            "verifications": verifications,
            "successful": successful,
            "failed": failed,
            "status": bulk_status,
            "refunded": round((final_base_cost * (1 - discount_pct)) * failed, 2)
            if failed > 0
            else 0,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Bulk verification creation failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Bulk purchase failed: {str(e)}")


@router.get("/{bulk_id}")
async def get_bulk_status(
    bulk_id: str,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Get status of bulk verification purchase."""

    try:
        # Find all verifications with this bulk_id
        verifications = db.query(Verification).filter(Verification.user_id == user_id).all()

        # Filter by bulk_id (if field exists)
        bulk_verifications = [v for v in verifications if hasattr(v, "bulk_id") and v.bulk_id == bulk_id]

        if not bulk_verifications:
            raise HTTPException(status_code=404, detail="Bulk purchase not found")

        # Calculate statistics
        total = len(bulk_verifications)
        completed = sum(1 for v in bulk_verifications if v.status == "completed")
        pending = sum(1 for v in bulk_verifications if v.status == "pending")
        failed = sum(1 for v in bulk_verifications if v.status in ["failed", "timeout", "cancelled"])

        return {
            "bulk_id": bulk_id,
            "total": total,
            "completed": completed,
            "pending": pending,
            "failed": failed,
            "verifications": [
                {
                    "id": v.id,
                    "phone_number": v.phone_number,
                    "status": v.status,
                    "cost": float(v.cost),
                    "created_at": v.created_at.isoformat(),
                }
                for v in bulk_verifications
            ],
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get bulk status: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get bulk status: {str(e)}")


@router.post("/{bulk_id}/cancel")
async def cancel_bulk_verification(
    bulk_id: str,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Cancel all pending verifications in bulk purchase."""

    try:
        # Find all verifications with this bulk_id
        verifications = db.query(Verification).filter(Verification.user_id == user_id).all()

        # Filter by bulk_id and pending status
        bulk_verifications = [
            v for v in verifications if hasattr(v, "bulk_id") and v.bulk_id == bulk_id and v.status == "pending"
        ]

        if not bulk_verifications:
            raise HTTPException(status_code=404, detail="No pending verifications found for this bulk purchase")

        # Cancel each verification
        cancelled = 0
        refund_total = Decimal("0")

        for verification in bulk_verifications:
            try:
                # Note: TextVerified doesn't have a cancel API like 5SIM
                # Simply mark as cancelled locally

                # Update status
                verification.status = "cancelled"
                refund_total += verification.cost
                cancelled += 1

            except Exception as e:
                logger.warning(f"Failed to cancel verification {verification.id}: {str(e)}")

        # Refund credits
        user = db.query(User).filter(User.id == user_id).first()
        if user:
            user.credits += refund_total

        db.commit()

        return {
            "bulk_id": bulk_id,
            "cancelled": cancelled,
            "refunded": float(refund_total),
            "message": f"Cancelled {cancelled} verifications, refunded ${refund_total:.2f}",
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to cancel bulk: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to cancel bulk purchase: {str(e)}")
