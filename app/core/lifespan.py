"""Application lifespan management - Minimal version for CI fix."""

import asyncio
import os
from contextlib import asynccontextmanager
from datetime import datetime, timezone

from app.core.database import engine
from app.core.init_admin import init_admin_user
from app.core.logging import get_logger
from app.models.base import Base

startup_logger = get_logger("startup")


def run_startup_initialization():
    """Run startup initialization tasks."""
    try:
        startup_logger.info("Running startup initialization...")
        init_admin_user()
        startup_logger.info("Startup initialization completed")
    except Exception as e:
        startup_logger.error(f"Startup initialization failed: {e}")


@asynccontextmanager
async def lifespan(app):
    """Application lifespan manager."""
    startup_logger.info("🚀 Starting Vrenum API...")

    try:
        # Initialize Sentry for error tracking
        from app.core.sentry import init_sentry

        init_sentry()

        # Initialize database
        startup_logger.info("Initializing database...")
        Base.registry.configure()
        Base.metadata.create_all(bind=engine, checkfirst=True)
        startup_logger.info("Database tables created successfully")

        # Create admin user if needed
        startup_logger.info("Checking admin user...")
        if os.getenv("TESTING") != "1":
            run_startup_initialization()
        startup_logger.info("Admin user verified")

        startup_logger.info("✅ Application startup completed successfully")

        # Initialize unified cache
        from app.core.unified_cache import cache

        try:
            await asyncio.wait_for(cache.connect(), timeout=10.0)
            startup_logger.info("Unified cache initialized")
        except asyncio.TimeoutError:
            startup_logger.warning(
                "Cache connection timeout - continuing without cache"
            )
        except Exception as e:
            startup_logger.warning(f"Cache initialization failed: {e}")

        # Pre-warm services and area codes cache (blocking — must complete before traffic)
        async def _prewarm():
            try:
                from app.services.textverified_service import TextVerifiedService

                tv = TextVerifiedService()
                if not tv.enabled:
                    startup_logger.error(
                        "⚠️  TextVerified is DISABLED — SMS verification will not work. "
                        "Set TEXTVERIFIED_API_KEY and TEXTVERIFIED_EMAIL in your environment."
                    )
                    return

                # Skip area codes prewarm if already cached (but services always re-fetch)
                startup_logger.info("Pre-warming TextVerified cache...")
                await asyncio.wait_for(
                    asyncio.gather(
                        tv.get_services_list(),
                        tv.get_area_codes_list(),
                        return_exceptions=True,
                    ),
                    timeout=20.0,
                )
                startup_logger.info("Cache pre-warming completed")
            except asyncio.TimeoutError:
                startup_logger.warning(
                    "Cache pre-warming timed out (will retry on next request)"
                )
            except Exception as e:
                startup_logger.warning(f"Cache pre-warming failed (non-critical): {e}")

        # Skip pre-warming in test mode — block startup until warm (max 20s)
        if os.getenv("TESTING") != "1":
            try:
                await asyncio.wait_for(_prewarm(), timeout=20.0)
            except asyncio.TimeoutError:
                startup_logger.warning("Pre-warm timed out — first request may be slow")
        else:
            startup_logger.info("Skipping TextVerified pre-warming in test mode")

        # Start SMS polling background service
        if os.getenv("TESTING") != "1":
            from app.services.refund_policy_enforcer import refund_policy_enforcer
            from app.services.sms_polling_service import sms_polling_service

            polling_task = asyncio.create_task(
                sms_polling_service.start_background_service()
            )
            startup_logger.info("✅ SMS polling background service started")

            # Start refund policy enforcer (backup to polling service)
            try:
                enforcer_task = asyncio.create_task(
                    refund_policy_enforcer.start_enforcement()
                )
                startup_logger.info("✅ Refund policy enforcer started (5-min backup)")
            except Exception as e:
                startup_logger.warning(
                    f"⚠️  Refund policy enforcer failed to start: {e}"
                )
                # Continue startup even if enforcer fails

            # Start institutional health audit loop (V6.0 Mastery)
            from app.services.providers.provider_health_check import (
                start_health_audit_loop,
            )

            asyncio.create_task(start_health_audit_loop())
            startup_logger.info(
                "✅ Institutional health audit loop started (every 4 hours)"
            )

            # Start daily growth snapshot loop (Institutional Mastery)
            async def start_daily_snapshot_loop():
                while True:
                    try:
                        from app.core.database import get_session_local
                        from app.services.target_tracking_service import (
                            TargetTrackingService,
                        )

                        # Use sync session correctly
                        SessionLocal = get_session_local()
                        db = SessionLocal()
                        try:
                            service = TargetTrackingService(db)
                            snapshot = await service.record_daily_snapshot()
                            if snapshot:
                                startup_logger.info(
                                    f"✅ Midnight growth snapshot recorded for {snapshot.snapshot_date}"
                                )
                        finally:
                            db.close()
                    except Exception as e:
                        startup_logger.error(f"❌ Daily snapshot failed: {e}")

                    # Sleep until next midnight (approx 24h)
                    await asyncio.sleep(86400)

            asyncio.create_task(start_daily_snapshot_loop())
            startup_logger.info("✅ Daily growth snapshotting active (24h loop)")

            # Rental expiry monitor (15-min loop)
            async def start_rental_expiry_loop():
                while True:
                    try:
                        from datetime import datetime, timezone

                        from app.core.database import SessionLocal
                        from app.models.verification import NumberRental

                        with SessionLocal() as db:
                            now = datetime.now(timezone.utc)
                            # Mark expired rentals
                            expired = (
                                db.query(NumberRental)
                                .filter(
                                    NumberRental.status == "active",
                                    NumberRental.expires_at <= now,
                                )
                                .all()
                            )
                            for r in expired:
                                r.status = "expired"
                                r.released_at = now
                            if expired:
                                db.commit()
                                startup_logger.info(
                                    f"Marked {len(expired)} rental(s) as expired"
                                )

                            # Send expiry warnings (1hr window)
                            from datetime import timedelta

                            warning_window = now + timedelta(hours=1)
                            expiring_soon = (
                                db.query(NumberRental)
                                .filter(
                                    NumberRental.status == "active",
                                    NumberRental.expires_at <= warning_window,
                                    NumberRental.expires_at > now,
                                    NumberRental.warning_sent == False,
                                )
                                .all()
                            )
                            for r in expiring_soon:
                                try:
                                    from app.services.notification_dispatcher import (
                                        NotificationDispatcher,
                                    )

                                    dispatcher = NotificationDispatcher(db)
                                    await dispatcher.send_notification(
                                        user_id=r.user_id,
                                        notification_type="rental_expiring_soon",
                                        data={
                                            "phone_number": r.phone_number,
                                            "service": r.service_name,
                                            "expires_at": r.expires_at.isoformat(),
                                        },
                                    )
                                    r.warning_sent = True
                                except Exception:
                                    pass
                            if expiring_soon:
                                db.commit()
                    except Exception as e:
                        startup_logger.error(f"Rental expiry monitor error: {e}")
                    await asyncio.sleep(900)  # 15 minutes

            asyncio.create_task(start_rental_expiry_loop())
            startup_logger.info("✅ Rental expiry monitor started (15-min loop)")

            # Abandoned payment cleanup (hourly)
            # Paystack expires checkouts after ~30min but never fires a webhook.
            # Any PaymentLog still in pending/processing after 2 hours is abandoned.
            async def start_abandoned_payment_cleanup():
                while True:
                    try:
                        from datetime import datetime, timedelta, timezone

                        from app.core.database import SessionLocal
                        from app.models.transaction import PaymentLog, Transaction

                        with SessionLocal() as db:
                            cutoff = datetime.now(timezone.utc) - timedelta(hours=2)
                            stale = (
                                db.query(PaymentLog)
                                .filter(
                                    PaymentLog.state.in_(["pending", "processing"]),
                                    PaymentLog.processing_started_at <= cutoff,
                                    # Never auto-cancel crypto intents — require admin review
                                    PaymentLog.payment_method.is_(None),
                                )
                                .all()
                            )
                            for p in stale:
                                p.state = "abandoned"
                                tx = (
                                    db.query(Transaction)
                                    .filter(Transaction.reference == p.reference)
                                    .first()
                                )
                                if tx and tx.status == "pending":
                                    tx.status = "abandoned"
                            if stale:
                                db.commit()
                                startup_logger.info(
                                    f"Marked {len(stale)} abandoned Paystack checkout(s)"
                                )
                    except Exception as e:
                        startup_logger.error(f"Abandoned payment cleanup error: {e}")
                    await asyncio.sleep(3600)  # hourly

            asyncio.create_task(start_abandoned_payment_cleanup())
            startup_logger.info("✅ Abandoned payment cleanup started (hourly)")

            # Revenue-zero alert (daily at 18:00 UTC)
            async def start_revenue_zero_monitor():
                while True:
                    try:
                        now = datetime.now(timezone.utc)
                        # Sleep until next 18:00 UTC
                        target = now.replace(hour=18, minute=0, second=0, microsecond=0)
                        if now >= target:
                            target = target.replace(day=target.day + 1)
                        await asyncio.sleep((target - now).total_seconds())

                        from app.core.database import SessionLocal
                        from app.services.alerting_service import alerting_service

                        with SessionLocal() as db:
                            fired = await alerting_service.check_revenue_zero(db)
                            if fired:
                                startup_logger.warning("🚨 Revenue-zero alert fired")
                    except Exception as e:
                        startup_logger.error(f"Revenue-zero monitor error: {e}")
                    await asyncio.sleep(3600)  # retry after 1h on error

            asyncio.create_task(start_revenue_zero_monitor())
            startup_logger.info("✅ Revenue-zero monitor started (daily at 18:00 UTC)")

            # Daily + weekly digest emails
            async def start_digest_scheduler():
                while True:
                    try:
                        from datetime import timedelta

                        now = datetime.now(timezone.utc)
                        # Sleep until next 08:00 UTC
                        target = now.replace(hour=8, minute=0, second=0, microsecond=0)
                        if now >= target:
                            target += timedelta(days=1)
                        await asyncio.sleep((target - now).total_seconds())

                        now = datetime.now(timezone.utc)
                        from app.core.database import SessionLocal
                        from app.models.notification import Notification
                        from app.models.user import User
                        from app.services.email_service import email_service

                        is_monday = now.weekday() == 0
                        cutoff = now - timedelta(days=7 if is_monday else 1)

                        with SessionLocal() as db:
                            users = (
                                db.query(User)
                                .filter(
                                    User.is_active.is_(True),
                                    User.is_admin.is_(False),
                                )
                                .all()
                            )
                            for user in users:
                                try:
                                    notifs = (
                                        db.query(Notification)
                                        .filter(
                                            Notification.user_id == user.id,
                                            Notification.is_read.is_(False),
                                            Notification.created_at >= cutoff,
                                        )
                                        .order_by(Notification.created_at.desc())
                                        .limit(20)
                                        .all()
                                    )
                                    if not notifs:
                                        continue
                                    name = getattr(user, "display_name", None)
                                    if is_monday:
                                        stats = {"unread_notifications": len(notifs)}
                                        await email_service.send_weekly_digest_email(
                                            user.email, notifs, stats, user_name=name
                                        )
                                    else:
                                        await email_service.send_daily_digest_email(
                                            user.email, notifs, user_name=name
                                        )
                                except Exception as ue:
                                    startup_logger.warning(
                                        f"Digest failed for {user.id}: {ue}"
                                    )
                    except Exception as e:
                        startup_logger.error(f"Digest scheduler error: {e}")
                    # Loop back — next sleep calculated at top

            asyncio.create_task(start_digest_scheduler())
            startup_logger.info(
                "✅ Digest email scheduler started (daily 08:00 UTC, weekly Mon)"
            )

            from app.services.stock_monitor import run_stock_monitor

            asyncio.create_task(run_stock_monitor())
            startup_logger.info("✅ Service stock monitor started (15-min refresh)")

            # Area code cache refresh (every 23h — before 24h TTL expires)
            async def run_area_code_refresh():
                while True:
                    await asyncio.sleep(23 * 3600)
                    try:
                        from app.core.unified_cache import cache as _cache
                        from app.services.textverified_service import (
                            _AC_STATE_CACHE_KEY,
                            _AREA_CODES_CACHE_KEY,
                        )
                        from app.services.textverified_service import (
                            TextVerifiedService as _TVS,
                        )

                        tv = _TVS()
                        if tv.enabled:
                            await _cache.set(_AREA_CODES_CACHE_KEY, None, 1)
                            await _cache.set(_AC_STATE_CACHE_KEY, None, 1)
                            await tv.get_area_codes_list()
                            await tv._get_area_codes_by_state()
                            startup_logger.info(
                                "✅ Area code cache refreshed (23h loop)"
                            )
                    except Exception as e:
                        startup_logger.warning(f"Area code refresh failed: {e}")

            asyncio.create_task(run_area_code_refresh())
            startup_logger.info("✅ Area code cache refresh started (23h loop)")

            # Weekly TextVerified margin reconciliation (Monday 09:00 UTC)
            async def start_margin_reconciliation_loop():
                while True:
                    try:
                        now = datetime.now(timezone.utc)
                        # Next Monday 09:00 UTC
                        days_until_monday = (7 - now.weekday()) % 7 or 7
                        target = now.replace(hour=9, minute=0, second=0, microsecond=0)
                        target = target.replace(day=now.day + days_until_monday)
                        await asyncio.sleep((target - now).total_seconds())

                        from app.core.database import SessionLocal
                        from app.services.provider_settlement_service import (
                            ProviderSettlementService,
                        )

                        with SessionLocal() as db:
                            svc = ProviderSettlementService(db)
                            result = await svc.check_margin(db)
                            startup_logger.info(
                                f"TV margin check: {result['margin_pct']:.1f}% "
                                f"(revenue=${result['platform_revenue']:.2f} cost=${result['tv_cost']:.2f})"
                            )
                    except Exception as e:
                        startup_logger.error(f"Margin reconciliation error: {e}")
                    await asyncio.sleep(3600)  # retry after 1h on error

            asyncio.create_task(start_margin_reconciliation_loop())
            startup_logger.info(
                "✅ TV margin reconciliation started (weekly Monday 09:00 UTC)"
            )

            # Month-end revenue target alert (last day of month 20:00 UTC)
            async def start_month_end_target_loop():
                while True:
                    try:
                        import calendar
                        from datetime import timedelta

                        now = datetime.now(timezone.utc)
                        # Last day of current month at 20:00 UTC
                        last_day = calendar.monthrange(now.year, now.month)[1]
                        target = now.replace(
                            day=last_day, hour=20, minute=0, second=0, microsecond=0
                        )
                        if now >= target:
                            # Already past — aim for next month's last day
                            next_month = now.replace(day=1) + timedelta(days=32)
                            last_day = calendar.monthrange(
                                next_month.year, next_month.month
                            )[1]
                            target = next_month.replace(
                                day=last_day, hour=20, minute=0, second=0, microsecond=0
                            )
                        await asyncio.sleep((target - now).total_seconds())

                        from app.core.database import get_session_local
                        from app.services.target_tracking_service import (
                            TargetTrackingService,
                        )

                        SessionLocal = get_session_local()
                        with SessionLocal() as db:
                            svc = TargetTrackingService(db)
                            fired = await svc.check_month_end_target()
                            if fired:
                                startup_logger.warning(
                                    "🚨 Month-end revenue target alert fired"
                                )
                    except Exception as e:
                        startup_logger.error(f"Month-end target check error: {e}")
                    await asyncio.sleep(3600)  # retry after 1h on error

            asyncio.create_task(start_month_end_target_loop())
            startup_logger.info(
                "✅ Month-end revenue target alert started (last day of month 20:00 UTC)"
            )
        else:
            startup_logger.info("Skipping SMS polling in test mode")

    except Exception as e:
        startup_logger.error(f"Startup failed: {e}")
        raise

    # Application is running
    yield

    # Shutdown
    startup_logger.info("🛑 Shutting down Vrenum API...")
    if os.getenv("TESTING") != "1":
        from app.services.refund_policy_enforcer import refund_policy_enforcer
        from app.services.sms_polling_service import sms_polling_service

        await sms_polling_service.stop_background_service()
        await refund_policy_enforcer.stop_enforcement()
        startup_logger.info("✅ Background services stopped")
    from app.core.unified_cache import cache

    try:
        await cache.disconnect()
    except Exception as e:
        startup_logger.warning(f"Cache disconnect failed: {e}")
    startup_logger.info("✅ Shutdown completed")
