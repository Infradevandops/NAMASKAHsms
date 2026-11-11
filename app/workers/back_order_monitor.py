"""Back-order monitor worker — Sprint D-011/D-012.

Runs every 5 minutes. Polls TV reservations.details() for pending back-orders.
When a back-order transitions to active, deducts credits and notifies the user.
Also fires admin alert when queue depth >= 5 for any service.
"""

import asyncio
from collections import Counter
from datetime import datetime, timezone

from app.core.logging import get_logger

logger = get_logger(__name__)


async def check_back_orders() -> None:
    """Check all pending back-orders against TV and fulfill completed ones."""
    try:
        from app.core.database import AsyncSessionLocal
        from app.models.rental_back_order import RentalBackOrder
        from app.models.user import User
        from app.services.alerting_service import alerting_service
        from app.services.balance_service import BalanceService
        from app.services.notification_service import NotificationService
        from app.services.textverified_service import TextVerifiedService
        from sqlalchemy import select, func

        tv = TextVerifiedService()
        if not tv.enabled:
            return

        async with AsyncSessionLocal() as db:
            result = await db.execute(
                select(RentalBackOrder).where(RentalBackOrder.fulfilled_at.is_(None))
            )
            pending = result.scalars().all()

            if not pending:
                return

            logger.info(f"Back-order monitor: checking {len(pending)} pending orders")

            # Check admin alert threshold per service
            service_counts = Counter(o.service_name for o in pending)
            for service_name, count in service_counts.items():
                await alerting_service.send_back_order_queue_alert(service_name, count)

            for order in pending:
                try:
                    details = await asyncio.to_thread(
                        tv.client.reservations.details, order.tv_back_order_id
                    )
                    state = details.state.value if hasattr(details.state, "value") else str(details.state)

                    if state in ("renewableActive", "nonrenewableActive"):
                        # Fulfill: deduct credits and notify
                        user = await db.get(User, order.user_id)
                        if user:
                            user.credits = type(user.credits)(
                                float(user.credits or 0) - float(order.credits_held)
                            )

                        order.fulfilled_at = datetime.now(timezone.utc)
                        await db.commit()

                        # Notify user
                        try:
                            notif = NotificationService(db)
                            await notif.create_notification(
                                user_id=order.user_id,
                                type="rental_ready",
                                title="Your rental number is ready",
                                message=f"Your rental number for {order.service_name} is now active.",
                                data={"service_name": order.service_name},
                            )
                        except Exception as e:
                            logger.warning(f"Back-order notification failed: {e}")

                        logger.info(
                            f"Back-order fulfilled: user={order.user_id} "
                            f"service={order.service_name} id={order.tv_back_order_id}"
                        )

                except Exception as e:
                    logger.warning(
                        f"Back-order check failed for {order.tv_back_order_id}: {e}"
                    )

    except Exception as e:
        logger.error(f"Back-order monitor error: {e}")


async def run_back_order_monitor() -> None:
    """Background loop — checks back-orders every 5 minutes."""
    logger.info("✅ Back-order monitor started (5-min interval)")
    while True:
        try:
            await check_back_orders()
        except Exception as e:
            logger.warning(f"Back-order monitor loop error: {e}")
        await asyncio.sleep(300)
