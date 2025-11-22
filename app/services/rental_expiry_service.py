"""Background service for checking rental expiry and auto - extend."""
import asyncio
from datetime import datetime, timedelta, timezone
from decimal import Decimal

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.models.rental import Rental
from app.models.user import User

logger = get_logger(__name__)


class RentalExpiryService:
    """Service for managing rental expiry and auto - extend."""

    def __init__(self):
        self.running = False
        self.check_interval = 300  # Check every 5 minutes

    async def start_background_service(self):
        """Start the background service for checking rentals."""
        if self.running:
            logger.warning("Rental expiry service already running")
            return

        self.running = True
        logger.info("Starting rental expiry service")

        while self.running:
            try:
                await self.check_expiring_rentals()
                await asyncio.sleep(self.check_interval)
            except Exception as e:
                logger.error(f"Error in rental expiry service: {str(e)}")
                await asyncio.sleep(60)  # Wait 1 minute on error

    async def stop_background_service(self):
        """Stop the background service."""
        logger.info("Stopping rental expiry service")
        self.running = False

    async def check_expiring_rentals(self):
        """Check for expiring rentals and handle auto - extend."""
        try:
            async for db in get_async_session():
                # Find rentals expiring in the next hour
                one_hour_from_now = datetime.now(timezone.utc) + timedelta(hours=1)

                query = select(Rental).where(
                    and_(
                        Rental.status == "active",
                        Rental.expires_at <= one_hour_from_now,
                        Rental.expires_at > datetime.now(timezone.utc)
                    )
                )

                result = await db.execute(query)
                expiring_rentals = result.scalars().all()

                logger.info(f"Found {len(expiring_rentals)} expiring rentals")

                for rental in expiring_rentals:
                    await self.handle_expiring_rental(rental, db)

                await db.commit()

        except Exception as e:
            logger.error(f"Error checking expiring rentals: {str(e)}")

    async def handle_expiring_rental(self, rental: Rental, db: AsyncSession):
        """Handle a single expiring rental."""
        try:
            time_until_expiry = (rental.expires_at - datetime.now(timezone.utc)).total_seconds()

            # Send warning emails
            if 3000 < time_until_expiry <= 3600:  # Between 50 min and 1 hour
                await self.send_expiry_warning(rental, "1 hour")
                logger.info(f"Sent 1 - hour warning for rental {rental.id}")

            # Auto - extend if enabled and less than 10 minutes remaining
            if rental.auto_extend and time_until_expiry <= 600:  # 10 minutes
                await self.auto_extend_rental(rental, db)

        except Exception as e:
            logger.error(f"Error handling rental {rental.id}: {str(e)}")

    async def auto_extend_rental(self, rental: Rental, db: AsyncSession):
        """Auto - extend a rental."""
        try:
            # Get user
            user_query = select(User).where(User.id == rental.user_id)
            user_result = await db.execute(user_query)
            user = user_result.scalar_one_or_none()

            if not user:
                logger.error(f"User not found for rental {rental.id}")
                return

            # Calculate extension cost (same duration + renewal fee)
            extension_hours = rental.duration_hours
            extension_cost = self._calculate_rental_cost(extension_hours)
            renewal_fee = Decimal("5.00")
            total_cost = extension_cost + renewal_fee

            # Check if user has enough credits
            if user.credits < total_cost:
                logger.warning(
                    f"Insufficient credits for auto - extend: rental {rental.id}, "
                    f"required ${total_cost}, available ${user.credits}"
                )
                # Send notification about failed auto - extend
                await self.send_auto_extend_failed(rental, user, total_cost)
                # Disable auto - extend
                rental.auto_extend = False
                return

            # Extend rental
            rental.expires_at += timedelta(hours=extension_hours)
            rental.cost += total_cost
            user.credits -= total_cost

            logger.info(
                f"Auto - extended rental {rental.id} for {extension_hours} hours, "
                f"cost ${total_cost} (including ${renewal_fee} renewal fee)"
            )

            # Send confirmation
            await self.send_auto_extend_success(rental, user,
                                                extension_hours, total_cost)

        except Exception as e:
            logger.error(f"Error auto - extending rental {rental.id}: {str(e)}")

    def _calculate_rental_cost(self, duration_hours: int) -> Decimal:
        """Calculate rental cost based on duration."""
        if duration_hours <= 12:
            return Decimal("6.00")
        elif duration_hours <= 24:
            return Decimal("12.00")
        elif duration_hours <= 72:  # 3 days
            return Decimal("30.00")
        elif duration_hours <= 168:  # 1 week
            return Decimal("50.00")
        elif duration_hours <= 720:  # 1 month
            return Decimal("150.00")
        else:
            days = duration_hours / 24
            return Decimal(str(days * 5))

    async def send_expiry_warning(self, rental: Rental, time_remaining: str):
        """Send expiry warning email."""
        # TODO: Implement email sending
        logger.info(f"Would send expiry warning for rental {rental.id}: {time_remaining} remaining")

    async def send_auto_extend_success(
        self, rental: Rental, user: User, hours: int, cost: Decimal
    ):
        """Send auto - extend success notification."""
        # TODO: Implement email sending
        logger.info(
            f"Would send auto - extend success for rental {rental.id}: "
            f"extended {hours} hours for ${cost}"
        )

    async def send_auto_extend_failed(
        self, rental: Rental, user: User, required_cost: Decimal
    ):
        """Send auto - extend failed notification."""
        # TODO: Implement email sending
        logger.info(
            f"Would send auto - extend failed for rental {rental.id}: "
            f"insufficient credits (need ${required_cost}, have ${user.credits})"
        )


# Global instance
rental_expiry_service = RentalExpiryService()
