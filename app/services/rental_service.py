"""Rental service for managing SMS number rentals."""
import uuid
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import List

from fastapi import HTTPException
from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import (
    InsufficientCreditsError,
    RentalExpiredError,
    RentalNotFoundError,
    ExternalServiceError,
)
from app.core.logging import get_logger
from app.models.rental import Rental
from app.models.user import User
from app.schemas.rental import (
    RentalCreate,
    RentalExtend,
    RentalMessagesResponse,
    RentalResponse,
)
from app.services.textverified_service import TextVerifiedService

logger = get_logger(__name__)


class RentalService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_rental(
        self, user_id: str, rental_data: RentalCreate
    ) -> RentalResponse:
        """Create a new rental with 5SIM integration."""
        try:
            # Calculate rental cost based on duration
            # Pricing: $0.50/day base rate
            cost = self._calculate_rental_cost(rental_data.duration_hours)

            # Check user credits
            user = await self._get_user(user_id)
            if user.credits < cost:
                raise InsufficientCreditsError(
                    f"Insufficient credits. Required: ${cost:.2f}, Available: ${user.credits:.2f}"
                )

            # Initialize TextVerified service (primary SMS provider)
            textverified = TextVerifiedService()
            
            # Purchase rental from TextVerified
            try:
                # Get phone number from TextVerified
                phone_number = await textverified.get_phone_number(rental_data.country_code)
                activation_id = str(uuid.uuid4())  # Generate a unique ID for tracking
                
                logger.info(f"Rental purchased from TextVerified: {phone_number}")
                
            except ExternalServiceError as e:
                logger.error(f"TextVerified rental purchase failed: {str(e)}")
                raise HTTPException(
                    status_code=503,
                    detail=f"Failed to purchase rental number: {str(e)}"
                )

            # Create rental record
            rental = Rental(
                id=str(uuid.uuid4()),
                user_id=user_id,
                phone_number=phone_number,
                service_name=rental_data.service_name or "any",
                country_code=rental_data.country_code,
                expires_at=datetime.now(timezone.utc)
                + timedelta(hours=rental_data.duration_hours),
                cost=cost,
                duration_hours=rental_data.duration_hours,
                activation_id=str(activation_id),
                status="active",
                provider="textverified",
                auto_extend=getattr(rental_data, 'auto_extend', False)
            )

            # Deduct credits
            user.credits -= cost

            self.db.add(rental)
            await self.db.commit()
            await self.db.refresh(rental)

            logger.info(f"Rental created: {rental.id} for user {user_id}")

            return RentalResponse.from_orm(rental)

        except Exception as e:
            await self.db.rollback()
            if isinstance(e, (InsufficientCreditsError, RentalNotFoundError, HTTPException)):
                raise
            logger.error(f"Rental creation failed: {str(e)}")
            raise HTTPException(
                status_code=500, detail=f"Failed to create rental: {str(e)}"
            )
    
    def _calculate_rental_cost(self, duration_hours: int) -> Decimal:
        """
        Calculate rental cost based on duration.
        
        Pricing tiers:
        - 12 hours: $6
        - 24 hours: $12
        - 3 days: $30
        - 1 week: $50
        - 1 month: $150
        """
        if duration_hours <= 12:
            return Decimal("6.00")
        elif duration_hours <= 24:
            return Decimal("12.00")
        elif duration_hours <= 72:  # 3 days
            return Decimal("30.00")
        elif duration_hours <= 168:  # 1 week
            return Decimal("50.00")
        elif duration_hours <= 720:  # 1 month (30 days)
            return Decimal("150.00")
        else:
            # For longer durations, calculate at $5/day
            days = duration_hours / 24
            return Decimal(str(days * 5))

    async def get_active_rentals(self, user_id: str) -> List[RentalResponse]:
        """Get user's active rentals."""
        try:
            query = select(Rental).where(
                and_(
                    Rental.user_id == user_id,
                    Rental.status == "active",
                    Rental.expires_at > datetime.utcnow(),
                )
            )
            result = await self.db.execute(query)
            rentals = result.scalars().all()

            return [RentalResponse.from_orm(rental) for rental in rentals]

        except Exception as e:
            raise HTTPException(
                status_code=500, detail=f"Failed to get rentals: {str(e)}"
            )

    async def extend_rental(
        self, rental_id: str, user_id: str, extend_data: RentalExtend
    ) -> dict:
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
                raise InsufficientCreditsError("Insufficient credits for extension")

            # Extend rental
            rental.expires_at += timedelta(hours=extend_data.additional_hours)
            rental.duration_hours += extend_data.additional_hours
            user.credits -= extension_cost

            await self.db.commit()

            return {
                "extension_cost": float(extension_cost),
                "new_expires_at": rental.expires_at,
                "remaining_credits": float(user.credits),
            }

        except Exception as e:
            await self.db.rollback()
            if isinstance(
                e, (InsufficientCreditsError, RentalNotFoundError, RentalExpiredError)
            ):
                raise
            raise HTTPException(
                status_code=500, detail=f"Failed to extend rental: {str(e)}"
            )

    async def release_rental(self, rental_id: str, user_id: str) -> dict:
        """Release rental early with 50% refund."""
        try:
            rental = await self._get_rental(rental_id, user_id)

            if rental.is_expired:
                raise RentalExpiredError("Rental already expired")

            # Calculate refund (50% of remaining time)
            remaining_hours = rental.time_remaining_seconds / 3600
            refund = (rental.cost * Decimal("0.5")) * (
                remaining_hours / rental.duration_hours
            )

            # Update rental and user credits
            rental.status = "released"
            user = await self._get_user(user_id)
            user.credits += refund

            await self.db.commit()

            return {"refund": float(refund), "remaining_credits": float(user.credits)}

        except Exception as e:
            await self.db.rollback()
            if isinstance(e, (RentalNotFoundError, RentalExpiredError)):
                raise
            raise HTTPException(
                status_code=500, detail=f"Failed to release rental: {str(e)}"
            )

    async def get_rental_messages(
        self, rental_id: str, user_id: str
    ) -> RentalMessagesResponse:
        """Get SMS messages for rental from TextVerified."""
        try:
            rental = await self._get_rental(rental_id, user_id)

            # Get messages from TextVerified
            messages = []
            
            try:
                # TextVerified doesn't have a direct check_activation API like 5SIM
                # In a real implementation, you would store SMS messages as they arrive via webhook
                # For now, return an empty message list
                logger.info(f"Retrieved {len(messages)} messages for rental {rental_id}")
                
            except Exception as e:
                logger.error(f"Failed to get messages from TextVerified: {str(e)}")
                # Return empty messages instead of failing
                messages = []

            return RentalMessagesResponse(
                phone_number=rental.phone_number,
                service_name=rental.service_name,
                message_count=len(messages),
                messages=[msg["text"] for msg in messages],
            )

        except Exception as e:
            if isinstance(e, RentalNotFoundError):
                raise
            logger.error(f"Failed to get rental messages: {str(e)}")
            raise HTTPException(
                status_code=500, detail=f"Failed to get messages: {str(e)}"
            )

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
