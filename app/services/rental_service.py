"""Rental service for managing SMS number rentals."""
import uuid
from datetime import datetime, timedelta
from decimal import Decimal
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from fastapi import HTTPException

from app.models.rental import Rental
from app.models.user import User
from app.schemas.rental import RentalCreate, RentalExtend, RentalResponse, RentalMessagesResponse
from app.core.exceptions import InsufficientCreditsError, RentalNotFoundError, RentalExpiredError

class RentalService:
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def create_rental(self, user_id: str, rental_data: RentalCreate) -> RentalResponse:
        """Create a new rental."""
        try:
            # Calculate cost (base rate: $0.50/day)
            cost = Decimal("0.50") * (rental_data.duration_hours / 24)
            
            # Check user credits
            user = await self._get_user(user_id)
            if user.credits < cost:
                raise InsufficientCreditsError(f"Insufficient credits. Required: ${cost}, Available: ${user.credits}")
            
            # Create rental record
            rental = Rental(
                id=str(uuid.uuid4()),
                user_id=user_id,
                phone_number="+1234567890",  # Placeholder - integrate with 5SIM
                service_name=rental_data.service_name,
                country_code=rental_data.country_code,
                expires_at=datetime.utcnow() + timedelta(hours=rental_data.duration_hours),
                cost=cost,
                duration_hours=rental_data.duration_hours,
                activation_id=f"rental_{uuid.uuid4().hex[:8]}"
            )
            
            # Deduct credits
            user.credits -= cost
            
            self.db.add(rental)
            await self.db.commit()
            await self.db.refresh(rental)
            
            return RentalResponse.from_orm(rental)
            
        except Exception as e:
            await self.db.rollback()
            if isinstance(e, (InsufficientCreditsError, RentalNotFoundError)):
                raise
            raise HTTPException(status_code=500, detail=f"Failed to create rental: {str(e)}")
    
    async def get_active_rentals(self, user_id: str) -> List[RentalResponse]:
        """Get user's active rentals."""
        try:
            query = select(Rental).where(
                and_(
                    Rental.user_id == user_id,
                    Rental.status == "active",
                    Rental.expires_at > datetime.utcnow()
                )
            )
            result = await self.db.execute(query)
            rentals = result.scalars().all()
            
            return [RentalResponse.from_orm(rental) for rental in rentals]
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to get rentals: {str(e)}")
    
    async def extend_rental(self, rental_id: str, user_id: str, extend_data: RentalExtend) -> dict:
        """Extend rental duration."""
        try:
            rental = await self._get_rental(rental_id, user_id)
            
            if rental.is_expired:
                raise RentalExpiredError("Cannot extend expired rental")
            
            # Calculate extension cost
            extension_cost = Decimal("0.50") * (extend_data.additional_hours / 24)
            
            # Check user credits
            user = await self._get_user(user_id)
            if user.credits < extension_cost:
                raise InsufficientCreditsError(f"Insufficient credits for extension")
            
            # Extend rental
            rental.expires_at += timedelta(hours=extend_data.additional_hours)
            rental.duration_hours += extend_data.additional_hours
            user.credits -= extension_cost
            
            await self.db.commit()
            
            return {
                "extension_cost": float(extension_cost),
                "new_expires_at": rental.expires_at,
                "remaining_credits": float(user.credits)
            }
            
        except Exception as e:
            await self.db.rollback()
            if isinstance(e, (InsufficientCreditsError, RentalNotFoundError, RentalExpiredError)):
                raise
            raise HTTPException(status_code=500, detail=f"Failed to extend rental: {str(e)}")
    
    async def release_rental(self, rental_id: str, user_id: str) -> dict:
        """Release rental early with 50% refund."""
        try:
            rental = await self._get_rental(rental_id, user_id)
            
            if rental.is_expired:
                raise RentalExpiredError("Rental already expired")
            
            # Calculate refund (50% of remaining time)
            remaining_hours = rental.time_remaining_seconds / 3600
            refund = (rental.cost * Decimal("0.5")) * (remaining_hours / rental.duration_hours)
            
            # Update rental and user credits
            rental.status = "released"
            user = await self._get_user(user_id)
            user.credits += refund
            
            await self.db.commit()
            
            return {
                "refund": float(refund),
                "remaining_credits": float(user.credits)
            }
            
        except Exception as e:
            await self.db.rollback()
            if isinstance(e, (RentalNotFoundError, RentalExpiredError)):
                raise
            raise HTTPException(status_code=500, detail=f"Failed to release rental: {str(e)}")
    
    async def get_rental_messages(self, rental_id: str, user_id: str) -> RentalMessagesResponse:
        """Get SMS messages for rental."""
        try:
            rental = await self._get_rental(rental_id, user_id)
            
            # Placeholder - integrate with 5SIM to get actual messages
            messages = ["Welcome to WhatsApp", "Your verification code is 123456"]
            
            return RentalMessagesResponse(
                phone_number=rental.phone_number,
                service_name=rental.service_name,
                message_count=len(messages),
                messages=messages
            )
            
        except Exception as e:
            if isinstance(e, RentalNotFoundError):
                raise
            raise HTTPException(status_code=500, detail=f"Failed to get messages: {str(e)}")
    
    async def _get_rental(self, rental_id: str, user_id: str) -> Rental:
        """Get rental by ID and user ID."""
        query = select(Rental).where(
            and_(Rental.id == rental_id, Rental.user_id == user_id)
        )
        result = await self.db.execute(query)
        rental = result.scalar_one_or_none()
        
        if not rental:
            raise RentalNotFoundError("Rental not found")
        
        return rental
    
    async def _get_user(self, user_id: str) -> User:
        """Get user by ID."""
        query = select(User).where(User.id == user_id)
        result = await self.db.execute(query)
        user = result.scalar_one_or_none()
        
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        return user