"""
Email outbox worker — supervised, lease-based, bounded retries.

Start via lifespan.py:
    from app.services.email_outbox_worker import run_outbox_worker
    asyncio.create_task(run_outbox_worker())
"""

import asyncio
import json
import socket
import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional

from sqlalchemy.orm import Session

from app.core.logging import get_logger
from app.models.email_outbox import EmailOutbox
from app.services.email_classes import EmailClass, is_suppressible_by_opt_out

logger = get_logger(__name__)

_WORKER_ID = f"{socket.gethostname()}-{uuid.uuid4().hex[:8]}"
_BATCH_SIZE = 10
_LEASE_SECONDS = 120
_POLL_INTERVAL = 15  # seconds between sweeps
_BACKOFF_BASE = 60   # seconds; doubles each retry up to ~32 min


def _next_attempt_delay(attempt: int) -> int:
    """Exponential backoff with jitter: 60s, 120s, 240s, 480s, 960s."""
    import random
    delay = min(_BACKOFF_BASE * (2 ** attempt), 960)
    return int(delay + random.uniform(0, delay * 0.1))


def _claim_batch(db: Session) -> list:
    """Atomically claim up to _BATCH_SIZE pending rows."""
    now = datetime.now(timezone.utc)
    lease_exp = now + timedelta(seconds=_LEASE_SECONDS)

    rows = (
        db.query(EmailOutbox)
        .filter(
            EmailOutbox.status.in_(["pending", "retry_wait"]),
            (EmailOutbox.next_attempt_at == None) | (EmailOutbox.next_attempt_at <= now),  # noqa: E711
        )
        .with_for_update(skip_locked=True)
        .limit(_BATCH_SIZE)
        .all()
    )

    for row in rows:
        row.status = "processing"
        row.lease_owner = _WORKER_ID
        row.lease_expires_at = lease_exp

    if rows:
        db.commit()
    return rows


def _recover_expired_leases(db: Session) -> int:
    """Reset rows whose lease expired without completion."""
    now = datetime.now(timezone.utc)
    stale = (
        db.query(EmailOutbox)
        .filter(
            EmailOutbox.status == "processing",
            EmailOutbox.lease_expires_at <= now,
        )
        .all()
    )
    for row in stale:
        row.status = "retry_wait"
        row.lease_owner = None
        row.lease_expires_at = None
        row.next_attempt_at = datetime.now(timezone.utc) + timedelta(
            seconds=_next_attempt_delay(row.attempt_count)
        )
    if stale:
        db.commit()
        logger.warning(f"Recovered {len(stale)} expired leases")
    return len(stale)


async def _process_row(row: EmailOutbox, db: Session) -> None:
    """Send one outbox row, update status."""
    now = datetime.now(timezone.utc)
    row.attempt_count += 1

    # Check optional preference before sending
    if is_suppressible_by_opt_out(EmailClass(row.email_class)):
        if row.category:
            try:
                from app.services.email_preference_policy import EmailPreferencePolicy
                # Extract user_id from source_event_id if encoded, else skip check
                # (we don't store user_id on outbox to minimise PII surface)
                # Policy check is best-effort here; primary check is at enqueue time
                pass
            except Exception:
                pass

    # Attempt send
    try:
        from app.services.email_service import email_service

        payload = json.loads(row.payload_json or "{}")
        subject = payload.get("subject", "(no subject)")
        html_body = payload.get("html_body", "")

        sent = await email_service._send(row.recipient_email, subject, html_body)

        if sent:
            row.status = "provider_accepted"
            row.accepted_at = now
            row.last_error = None
            logger.info(f"Outbox {row.id} sent to {row.recipient_email}")
        else:
            raise RuntimeError("email_service._send returned False")

    except Exception as exc:
        err = str(exc)[:500]
        row.last_error = err
        logger.warning(f"Outbox {row.id} attempt {row.attempt_count} failed: {err}")

        if row.attempt_count >= row.max_attempts:
            row.status = "failed_permanent"
            row.terminal_at = now
            logger.error(
                f"Outbox {row.id} dead-lettered after {row.attempt_count} attempts"
            )
        else:
            row.status = "retry_wait"
            row.next_attempt_at = now + timedelta(
                seconds=_next_attempt_delay(row.attempt_count)
            )

    row.lease_owner = None
    row.lease_expires_at = None
    db.commit()


async def run_outbox_worker() -> None:
    """Background loop — polls for pending outbox rows every _POLL_INTERVAL seconds."""
    logger.info(f"Email outbox worker started (id={_WORKER_ID})")
    while True:
        try:
            from app.core.database import SessionLocal

            with SessionLocal() as db:
                _recover_expired_leases(db)
                rows = _claim_batch(db)
                if rows:
                    await asyncio.gather(
                        *[_process_row(row, db) for row in rows],
                        return_exceptions=True,
                    )
        except Exception as exc:
            logger.error(f"Outbox worker sweep error: {exc}")
        await asyncio.sleep(_POLL_INTERVAL)
