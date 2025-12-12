"""TextVerified rentals endpoints."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Optional
from pydantic import BaseModel

from app.core.database import get_db
from app.core.logging import get_logger
from app.core.dependencies import get_current_user_id

logger = get_logger(__name__)
router = APIRouter(prefix="/rentals", tags=["Rentals"])


class CreateRentalRequest(BaseModel):
    service: str
    duration_days: int = 7
    renewable: bool = False
    area_code: Optional[str] = None
    carrier: Optional[str] = None


class ExtendRentalRequest(BaseModel):
    duration_days: int = 7


@router.get("")
async def get_user_rentals(
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """Get user's active rentals from TextVerified."""
    try:
        from app.services.textverified_integration import get_textverified_integration
        
        integration = get_textverified_integration()
        rentals = await integration.get_active_rentals()
        
        logger.info(f"Retrieved {len(rentals)} rentals for user {user_id}")
        
        return {
            "success": True,
            "rentals": rentals,
            "total": len(rentals)
        }
        
    except Exception as e:
        logger.error(f"Failed to get rentals: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to load rentals: {str(e)}")


@router.post("")
async def create_rental(
    request: CreateRentalRequest,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """Create new phone rental (Starter+ only)."""
    try:
        from app.services.textverified_integration import get_textverified_integration
        from app.models.user import User
        from app.models.transaction import Transaction
        from app.models.rental import Rental
        import uuid
        from datetime import datetime, timedelta, timezone
        
        # Get user
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Check tier access
        user_tier = getattr(user, 'subscription_tier', 'freemium')
        if user_tier == 'freemium':
            raise HTTPException(
                status_code=402,
                detail="Rentals require Starter tier or higher. Upgrade to access this feature."
            )
        
        # Check carrier filtering (Turbo only)
        if request.carrier and user_tier != 'turbo':
            raise HTTPException(
                status_code=402,
                detail="Carrier/ISP filtering requires Turbo tier. Upgrade to access this feature."
            )
        
        # Calculate cost based on duration
        cost_map = {1: 2.50, 7: 15.00, 30: 50.00}
        cost = cost_map.get(request.duration_days, 15.00)
        
        # Check balance
        if user.credits < cost:
            raise HTTPException(status_code=402, detail=f"Insufficient balance. Required: ${cost}, Available: ${user.credits}")
        
        # Create rental via TextVerified
        integration = get_textverified_integration()
        rental_data = await integration.create_rental(
            service=request.service,
            duration_days=request.duration_days,
            renewable=request.renewable,
            area_code=request.area_code,
            carrier=request.carrier
        )
        
        # Deduct cost from user balance
        user.credits -= cost
        
        # Create rental record in database
        rental = Rental(
            id=str(uuid.uuid4()),
            user_id=user_id,
            phone_number=rental_data.get('phone_number'),
            service_name=request.service,
            country_code='US',
            expires_at=datetime.now(timezone.utc) + timedelta(days=request.duration_days),
            cost=cost,
            duration_hours=request.duration_days * 24,
            activation_id=rental_data.get('id'),
            status='active',
            provider='textverified',
            auto_extend=request.renewable
        )
        db.add(rental)
        
        # Log transaction
        transaction = Transaction(
            id=str(uuid.uuid4()),
            user_id=user_id,
            amount=-cost,
            type="rental",
            description=f"Rental: {request.service} for {request.duration_days} days",
            created_at=datetime.utcnow()
        )
        db.add(transaction)
        db.commit()
        
        logger.info(f"Rental created: {rental.id} for user {user_id}, cost: ${cost}")
        
        return {
            "success": True,
            "id": rental.id,
            "phone_number": rental.phone_number,
            "service": request.service,
            "expires_at": rental.expires_at.isoformat(),
            "cost": float(cost),
            "balance_after": float(user.credits)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to create rental: {str(e)}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to create rental: {str(e)}")


@router.post("/{rental_id}/extend")
async def extend_rental(
    rental_id: str,
    request: ExtendRentalRequest,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """Extend rental duration."""
    try:
        from app.services.textverified_integration import get_textverified_integration
        from app.models.user import User
        from app.models.transaction import Transaction
        import uuid
        from datetime import datetime
        
        # Get user
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Extend rental via TextVerified
        integration = get_textverified_integration()
        result = await integration.extend_rental(rental_id, request.duration_days)
        
        cost = result.get('cost', 0)
        
        # Check balance
        if user.credits < cost:
            raise HTTPException(status_code=402, detail="Insufficient balance")
        
        # Deduct cost
        balance_before = user.credits
        user.credits -= cost
        balance_after = user.credits
        
        # Log transaction
        transaction = Transaction(
            id=str(uuid.uuid4()),
            user_id=user_id,
            amount=-cost,
            type="rental_extension",
            description=f"Rental extension: {rental_id} for {request.duration_days} days",
            created_at=datetime.utcnow()
        )
        db.add(transaction)
        db.commit()
        
        logger.info(f"Rental extended: {rental_id} for user {user_id}, cost: ${cost}")
        
        return {
            "success": True,
            **result,
            "balance_after": float(balance_after)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to extend rental: {str(e)}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to extend rental: {str(e)}")


@router.post("/{rental_id}/release")
async def release_rental(
    rental_id: str,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """Release rental early with 50% refund."""
    try:
        from app.models.rental import Rental
        from app.models.user import User
        from app.models.transaction import Transaction
        import uuid
        from datetime import datetime, timezone
        from decimal import Decimal
        
        # Get rental
        rental = db.query(Rental).filter(
            Rental.id == rental_id,
            Rental.user_id == user_id
        ).first()
        
        if not rental:
            raise HTTPException(status_code=404, detail="Rental not found")
        
        if rental.status != "active":
            raise HTTPException(status_code=410, detail="Rental is not active")
        
        # Check if expired
        if rental.expires_at < datetime.now(timezone.utc):
            raise HTTPException(status_code=410, detail="Rental already expired")
        
        # Calculate refund (50% of remaining time value)
        now = datetime.now(timezone.utc)
        total_seconds = (rental.expires_at - rental.created_at).total_seconds()
        remaining_seconds = (rental.expires_at - now).total_seconds()
        
        if remaining_seconds <= 0:
            raise HTTPException(status_code=410, detail="Rental already expired")
        
        # 50% refund of remaining time value
        refund_percentage = Decimal("0.5")
        time_percentage = Decimal(str(remaining_seconds / total_seconds))
        refund = Decimal(str(rental.cost)) * refund_percentage * time_percentage
        
        # Get user
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Update rental status
        rental.status = "released"
        
        # Refund credits
        user.credits += float(refund)
        
        # Log transaction
        transaction = Transaction(
            id=str(uuid.uuid4()),
            user_id=user_id,
            amount=float(refund),
            type="rental_refund",
            description=f"Rental release refund (50%): {rental_id}",
            created_at=datetime.utcnow()
        )
        db.add(transaction)
        db.commit()
        
        logger.info(f"Rental released: {rental_id} for user {user_id}, refund: ${refund}")
        
        return {
            "success": True,
            "refund": float(refund),
            "remaining_credits": float(user.credits),
            "message": f"Rental released. Refunded ${refund:.2f} (50% of remaining time)"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to release rental: {str(e)}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to release rental: {str(e)}")


@router.get("/active")
async def get_active_rentals(
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """Get user's active rentals."""
    try:
        from app.models.rental import Rental
        from datetime import datetime, timezone
        
        rentals = db.query(Rental).filter(
            Rental.user_id == user_id,
            Rental.status == "active",
            Rental.expires_at > datetime.now(timezone.utc)
        ).all()
        
        result = []
        for rental in rentals:
            remaining_seconds = (rental.expires_at - datetime.now(timezone.utc)).total_seconds()
            result.append({
                "id": rental.id,
                "phone_number": rental.phone_number,
                "service_name": rental.service_name,
                "country_code": rental.country_code,
                "expires_at": rental.expires_at.isoformat(),
                "time_remaining_seconds": max(0, int(remaining_seconds)),
                "cost": float(rental.cost),
                "status": rental.status
            })
        
        return result
    except ImportError:
        logger.warning("Rental model not available")
        return []
    except Exception as e:
        logger.error(f"Failed to get active rentals: {str(e)}")
        return []
