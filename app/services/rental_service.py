"""Rental service for long-term number reservations (V6.0 Institutional Grade).

Manages the complete lifecycle of a number rental:
  - Purchase (with balance check and atomic debit)
  - Cancel (with prorated refund)
  - Extend (with balance top-up)
  - Message retrieval (live polling from TextVerified)
  - Expiry monitor (background loop, warns at 30min mark, releases at expiry)
"""

import asyncio
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.core.logging import get_logger
from app.models.user import User
from app.models.verification import NumberRental
from app.services.balance_service import BalanceService
from app.services.pricing_calculator import PricingCalculator
from app.services.providers.provider_router import ProviderRouter

logger = get_logger(__name__)

# Expiry warning threshold: warn admin / user when ≤ 30 minutes remain
EXPIRY_WARNING_MINUTES = 30


class RentalService:
    """Service to manage long-term number rentals."""

    def __init__(self, db: Session):
        self.db = db
        self.provider_router = ProviderRouter()

    # ── Purchase ──────────────────────────────────────────────────────────────

    async def purchase_rental(
        self,
        user_id: str,
        service: str,
        country: str,
        duration_hours: float = 24.0,
    ) -> Dict[str, Any]:
        """Purchase a new number rental.

        Flow:
          1. Calculate cost via PricingCalculator
          2. Check and atomically debit balance
          3. Purchase reservation from TextVerified
          4. Persist NumberRental record
        """
        # 1. Get provider price for this service to estimate cost
        #    We fetch the service price from the cached list (same source as display).
        #    This lets us check balance BEFORE committing money at the provider.
        from app.services.textverified_service import TextVerifiedService

        tv = TextVerifiedService()
        estimated_provider_cost = None
        try:
            services = await tv.get_services_list()
            for s in services:
                if s["id"] == service:
                    estimated_provider_cost = s.get("price")
                    break
        except Exception as e:
            logger.warning(f"Could not fetch service price for rental estimate: {e}")

        # 2. Pre-flight balance check with estimated cost
        if estimated_provider_cost and estimated_provider_cost > 0:
            from app.core.config import get_settings

            est_cost = round(estimated_provider_cost * get_settings().price_markup, 2)
            balance_check = await BalanceService.check_sufficient_balance(
                user_id, est_cost, self.db
            )
            if not balance_check["sufficient"]:
                raise ValueError(
                    f"Insufficient balance. Estimated cost: ${est_cost:.2f}, "
                    f"Available: ${balance_check.get('current_balance', 0):.2f}"
                )

        # 3. Purchase from provider to get actual cost
        purchase_result = await self.provider_router.purchase_with_failover(
            db=self.db,
            service=service,
            country=country,
            capability="rental",
            duration_hours=duration_hours,
        )

        # 4. Calculate final cost using the actual provider cost
        provider_cost = getattr(purchase_result, "cost", None) or (
            purchase_result.cost if hasattr(purchase_result, "cost") else None
        )
        pricing = PricingCalculator.calculate_rental_cost(
            self.db, user_id, duration_hours, provider_cost=provider_cost
        )
        total_cost = pricing["total_cost"]

        # 5. Final balance check with actual cost (may differ from estimate)
        balance_check = await BalanceService.check_sufficient_balance(
            user_id, total_cost, self.db
        )
        if not balance_check["sufficient"]:
            # Cancel the reservation since user can't afford actual cost
            try:
                order_id = getattr(purchase_result, "order_id", None)
                if order_id:
                    await tv._cancel_safe(order_id)
            except Exception:
                pass
            raise ValueError(
                f"Insufficient balance. Required: ${total_cost:.2f}, "
                f"Available: ${balance_check.get('balance', 0):.2f}"
            )

        # 6. Debit balance (atomic)
        user = self.db.query(User).filter(User.id == user_id).first()
        success, error = await BalanceService.deduct_credits_for_verification(
            db=self.db,
            user=user,
            verification=None,
            cost=total_cost,
            service_name=f"Rental: {service}",
            country_code=country,
        )
        if not success:
            # Roll back the provider reservation on billing failure
            try:
                from app.services.textverified_service import TextVerifiedService

                tv = TextVerifiedService()
                if hasattr(purchase_result, "order_id") and purchase_result.order_id:
                    await tv._cancel_safe(purchase_result.order_id)
            except Exception as cancel_err:
                logger.error(
                    f"Failed to cancel reservation after billing failure: {cancel_err}"
                )
            raise RuntimeError(f"Credit deduction failed: {error}")

        # 7. Create Rental Record
        now = datetime.now(timezone.utc)
        rental = NumberRental(
            user_id=user_id,
            phone_number=purchase_result.phone_number,
            service_name=service,
            duration_hours=duration_hours,
            cost=total_cost,
            mode="always_ready",
            status="active",
            started_at=now,
            expires_at=now + timedelta(hours=duration_hours),
            auto_extend=False,
            warning_sent=False,
        )
        # Persist the provider's reservation ID so we can poll / cancel it later
        if hasattr(rental, "provider_reservation_id"):
            rental.provider_reservation_id = getattr(purchase_result, "order_id", None)

        self.db.add(rental)
        self.db.commit()
        self.db.refresh(rental)

        logger.info(
            f"Rental {rental.id} created for user {user_id}: "
            f"{rental.phone_number} ({service}) → expires {rental.expires_at.isoformat()}"
        )

        return {
            "success": True,
            "rental_id": rental.id,
            "phone_number": rental.phone_number,
            "service": service,
            "country": country,
            "duration_hours": duration_hours,
            "cost": total_cost,
            "started_at": rental.started_at.isoformat(),
            "expires_at": rental.expires_at.isoformat(),
            "status": rental.status,
        }

    # ── Cancel ────────────────────────────────────────────────────────────────

    async def cancel_rental(self, rental_id: int, user_id: str) -> Dict[str, Any]:
        """Cancel an active rental and issue a prorated refund.

        Prorated refund = unused_fraction × original_cost
        (min refund: $0.00, i.e. no negative refunds)
        """
        rental = (
            self.db.query(NumberRental)
            .filter(NumberRental.id == rental_id, NumberRental.user_id == user_id)
            .first()
        )
        if not rental:
            raise ValueError(f"Rental {rental_id} not found for user {user_id}")
        if rental.status != "active":
            raise ValueError(
                f"Rental {rental_id} is not active (status: {rental.status})"
            )

        now = datetime.now(timezone.utc)
        expires_at = rental.expires_at
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)

        # Prorated refund calculation
        total_duration = (
            expires_at - rental.started_at.replace(tzinfo=timezone.utc)
        ).total_seconds()
        remaining = max(0.0, (expires_at - now).total_seconds())
        unused_fraction = remaining / total_duration if total_duration > 0 else 0.0
        refund_amount = round(rental.cost * unused_fraction, 2)

        # Cancel at provider level
        cancelled_at_provider = False
        reservation_id = getattr(rental, "provider_reservation_id", None)
        if reservation_id:
            try:
                from app.services.textverified_service import TextVerifiedService

                tv = TextVerifiedService()
                cancelled_at_provider = await tv._cancel_safe(reservation_id)
            except Exception as e:
                logger.warning(f"Provider cancel failed for rental {rental_id}: {e}")

        # Update rental record
        rental.status = "cancelled"
        rental.released_at = now

        # Issue refund
        if refund_amount > 0:
            user = self.db.query(User).filter(User.id == user_id).first()
            if user:
                user.credits = round(user.credits + refund_amount, 6)
                logger.info(
                    f"Prorated refund of ${refund_amount:.2f} issued to user {user_id} "
                    f"for rental {rental_id}"
                )

        self.db.commit()

        return {
            "success": True,
            "rental_id": rental_id,
            "cancelled_at": now.isoformat(),
            "refund_amount": refund_amount,
            "cancelled_at_provider": cancelled_at_provider,
        }

    # ── Extend ────────────────────────────────────────────────────────────────

    async def extend_rental(
        self, rental_id: int, user_id: str, extra_hours: float
    ) -> Dict[str, Any]:
        """Extend a rental by `extra_hours`, debiting the cost difference."""
        rental = (
            self.db.query(NumberRental)
            .filter(NumberRental.id == rental_id, NumberRental.user_id == user_id)
            .first()
        )
        if not rental:
            raise ValueError(f"Rental {rental_id} not found for user {user_id}")
        if rental.status != "active":
            raise ValueError(
                f"Rental {rental_id} is not active (status: {rental.status})"
            )

        # Calculate extension cost: prorate from original rental's hourly rate
        # The original rental.cost was already provider_cost × markup
        original_hourly = rental.cost / max(rental.duration_hours, 1)
        extra_cost = round(original_hourly * extra_hours, 2)

        balance_check = await BalanceService.check_sufficient_balance(
            user_id, extra_cost, self.db
        )
        if not balance_check["sufficient"]:
            raise ValueError(
                f"Insufficient balance for extension. Required: ${extra_cost:.2f}"
            )

        # Extend at provider level
        reservation_id = getattr(rental, "provider_reservation_id", None)
        extended_at_provider = False
        if reservation_id:
            try:
                from app.services.textverified_service import TextVerifiedService

                tv = TextVerifiedService()
                extended_at_provider = await tv.extend_reservation(
                    reservation_id, extra_hours
                )
            except Exception as e:
                logger.error(f"Provider extension failed for rental {rental_id}: {e}")
                raise RuntimeError(f"Failed to extend rental at provider: {e}")

        # Debit balance
        user = self.db.query(User).filter(User.id == user_id).first()
        success, error = await BalanceService.deduct_credits_for_verification(
            db=self.db,
            user=user,
            verification=None,
            cost=extra_cost,
            service_name=f"Rental Extension: {rental.service_name}",
            country_code="US",
        )
        if not success:
            raise RuntimeError(f"Extension billing failed: {error}")

        # Update rental record
        old_expiry = rental.expires_at
        rental.expires_at = rental.expires_at + timedelta(hours=extra_hours)
        rental.duration_hours = rental.duration_hours + extra_hours
        rental.cost = rental.cost + extra_cost
        rental.warning_sent = False  # Reset warning flag for new window
        self.db.commit()

        return {
            "success": True,
            "rental_id": rental_id,
            "previous_expiry": old_expiry.isoformat() if old_expiry else None,
            "new_expiry": rental.expires_at.isoformat(),
            "extra_hours": extra_hours,
            "extra_cost": extra_cost,
            "extended_at_provider": extended_at_provider,
        }

    # ── Active Rentals ────────────────────────────────────────────────────────

    async def get_active_rentals(self, user_id: str) -> List[NumberRental]:
        """Get all active rentals for a user."""
        return (
            self.db.query(NumberRental)
            .filter(
                NumberRental.user_id == user_id,
                NumberRental.status == "active",
                NumberRental.expires_at > datetime.now(timezone.utc),
            )
            .order_by(NumberRental.expires_at.asc())
            .all()
        )

    async def get_rental(self, rental_id: int, user_id: str) -> Optional[NumberRental]:
        """Get a single rental by ID (user-scoped)."""
        return (
            self.db.query(NumberRental)
            .filter(NumberRental.id == rental_id, NumberRental.user_id == user_id)
            .first()
        )

    # ── Messages ──────────────────────────────────────────────────────────────

    async def check_rental_messages(
        self, rental_id: int, user_id: Optional[str] = None
    ) -> List[Dict]:
        """Fetch all messages received on a rental number from TextVerified.

        Returns a list of normalized message dicts:
          {id, text, code, received_at, service_name}
        """
        query = self.db.query(NumberRental).filter(NumberRental.id == rental_id)
        if user_id:
            query = query.filter(NumberRental.user_id == user_id)
        rental = query.first()

        if not rental:
            return []

        reservation_id = getattr(rental, "provider_reservation_id", None)
        if not reservation_id:
            logger.warning(
                f"Rental {rental_id} has no provider_reservation_id — "
                "cannot fetch messages. Number may have been provisioned before V6.0."
            )
            return []

        try:
            from app.services.textverified_service import TextVerifiedService

            tv = TextVerifiedService()
            raw_messages = await tv.get_reservation_messages(reservation_id)

            # Normalize and annotate with service context
            return [
                {
                    "id": m.get("id"),
                    "text": m.get("text", ""),
                    "code": m.get("code"),
                    "received_at": m.get("received_at"),
                    "service_name": rental.service_name,
                    "phone_number": rental.phone_number,
                }
                for m in raw_messages
            ]
        except Exception as e:
            logger.error(f"Failed to fetch rental messages for rental {rental_id}: {e}")
            return []

    # ── Expiry Check ──────────────────────────────────────────────────────────

    async def check_expiry_status(self, rental_id: int, user_id: str) -> Dict[str, Any]:
        """Check expiry status for a specific rental."""
        reservation_id = None

        rental = await self.get_rental(rental_id, user_id)
        if not rental:
            raise ValueError(f"Rental {rental_id} not found")

        reservation_id = getattr(rental, "provider_reservation_id", None)

        if reservation_id:
            try:
                from app.services.textverified_service import TextVerifiedService

                tv = TextVerifiedService()
                provider_status = await tv.check_reservation_expiry(reservation_id)
                return {
                    "rental_id": rental_id,
                    "phone_number": rental.phone_number,
                    "expires_at": rental.expires_at.isoformat(),
                    **provider_status,
                }
            except Exception:
                pass

        # Fallback: calculate from DB record
        now = datetime.now(timezone.utc)
        expires_at = rental.expires_at
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)
        remaining_minutes = (expires_at - now).total_seconds() / 60

        return {
            "rental_id": rental_id,
            "phone_number": rental.phone_number,
            "expires_at": expires_at.isoformat(),
            "remaining_minutes": remaining_minutes,
            "is_critical": remaining_minutes < EXPIRY_WARNING_MINUTES,
            "status": rental.status,
        }


# ── Background Expiry Monitor ─────────────────────────────────────────────────


async def start_rental_expiry_monitor():
    """Background loop — checks rental expiry every 30 minutes.

    - Emits a warning log when a rental has ≤ 30 minutes remaining.
    - Marks expired rentals as 'expired' in the database.
    """
    logger.info("🔔 Rental expiry monitor started (30-min interval).")
    while True:
        await _run_expiry_check()
        await asyncio.sleep(30 * 60)


async def _run_expiry_check():
    """Single-pass expiry check across all active rentals."""
    db = None
    try:
        db = SessionLocal()
        now = datetime.now(timezone.utc)

        active_rentals = (
            db.query(NumberRental).filter(NumberRental.status == "active").all()
        )

        expired_count = 0
        warning_count = 0

        for rental in active_rentals:
            expires_at = rental.expires_at
            if expires_at.tzinfo is None:
                expires_at = expires_at.replace(tzinfo=timezone.utc)

            remaining = (expires_at - now).total_seconds() / 60

            if remaining <= 0:
                # Mark as expired
                rental.status = "expired"
                rental.released_at = now
                expired_count += 1
                logger.info(
                    f"Rental {rental.id} ({rental.phone_number}) marked as expired."
                )

            elif remaining <= EXPIRY_WARNING_MINUTES and not rental.warning_sent:
                # Issue warning
                rental.warning_sent = True
                warning_count += 1
                logger.warning(
                    f"⚠️ Rental {rental.id} ({rental.phone_number}) expiring in "
                    f"{remaining:.0f} min. User: {rental.user_id}"
                )
                # Log to ActivityLog for admin dashboard visibility
                try:
                    from app.models.system import ActivityLog

                    log = ActivityLog(
                        user_id=rental.user_id,
                        action="RENTAL_EXPIRY_WARNING",
                        element=str(rental.id),
                        status="WARNING",
                        details=f"Number {rental.phone_number} expires in {remaining:.0f} min.",
                    )
                    db.add(log)
                except Exception as log_err:
                    logger.warning(
                        f"Failed to log expiry warning to ActivityLog: {log_err}"
                    )

        if expired_count > 0 or warning_count > 0:
            db.commit()
            logger.info(
                f"Expiry check: {expired_count} expired, {warning_count} warnings issued."
            )

    except Exception as e:
        logger.error(f"Rental expiry check failed: {e}")
    finally:
        if db:
            db.close()
