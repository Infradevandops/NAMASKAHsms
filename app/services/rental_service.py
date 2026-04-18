"""Rental service for long-term number reservations."""

import asyncio
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional
from sqlalchemy.orm import Session

from app.core.logging import get_logger
from app.models.verification import NumberRental
from app.models.user import User
from app.services.balance_service import BalanceService
from app.services.pricing_calculator import PricingCalculator
from app.services.providers.provider_router import ProviderRouter

logger = get_logger(__name__)

class RentalService:
    """Service to manage long-term number rentals."""

    def __init__(self, db: Session):
        self.db = db
        self.provider_router = ProviderRouter()

    async def purchase_rental(
        self, 
        user_id: str, 
        service: str, 
        country: str, 
        duration_hours: float = 24.0
    ) -> Dict:
        """Purchase a new number rental."""
        # 1. Calculate cost
        pricing = PricingCalculator.calculate_rental_cost(self.db, user_id, duration_hours)
        total_cost = pricing["total_cost"]

        # 2. Check balance
        balance_check = await BalanceService.check_sufficient_balance(user_id, total_cost, self.db)
        if not balance_check["sufficient"]:
            raise ValueError(f"Insufficient balance. Required: ${total_cost:.2f}")

        # 3. Attempt purchase from provider (TextVerified Reservations primary)
        # Note: We need to extend ProviderRouter/Adapters to support 'rental' capability
        purchase_result = await self.provider_router.purchase_with_failover(
            db=self.db,
            service=service,
            country=country,
            capability="rental",
            duration_hours=duration_hours
        )

        # 4. Deduct balance
        user = self.db.query(User).filter(User.id == user_id).first()
        success, error = await BalanceService.deduct_credits_for_verification(
            db=self.db,
            user=user,
            verification=None, # Rental doesn't have a single verification record yet
            cost=total_cost,
            service_name=f"Rental: {service}",
            country_code=country
        )
        if not success:
            raise RuntimeError(f"Credit deduction failed: {error}")

        # 5. Create Rental Record
        rental = NumberRental(
            user_id=user_id,
            phone_number=purchase_result.phone_number,
            service_name=service,
            duration_hours=duration_hours,
            cost=total_cost,
            started_at=datetime.now(timezone.utc),
            expires_at=datetime.now(timezone.utc) + timedelta(hours=duration_hours),
            status="active",
            auto_extend=False
        )
        self.db.add(rental)
        self.db.commit()

        return {
            "success": True,
            "rental_id": rental.id,
            "phone_number": rental.phone_number,
            "expires_at": rental.expires_at.isoformat()
        }

    async def get_active_rentals(self, user_id: str) -> List[NumberRental]:
        """Get all active rentals for a user."""
        return self.db.query(NumberRental).filter(
            NumberRental.user_id == user_id,
            NumberRental.status == "active",
            NumberRental.expires_at > datetime.now(timezone.utc)
        ).all()

    async def check_rental_messages(self, rental_id: int) -> List[Dict]:
        """Fetch messages received on a rental number."""
        rental = self.db.query(NumberRental).filter(NumberRental.id == rental_id).first()
        if not rental:
            return []

        # Logic to call provider-specific message check for rentals
        # This will be implemented in the adapters
        return []
