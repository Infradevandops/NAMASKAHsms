"""TextVerified SMS webhook receiver.

TV POSTs here when an SMS arrives on any of our verification numbers.
This eliminates polling — SMS is delivered instantly via WebSocket to the user's browser.

TV retries on failure. After repeated failures TV auto-disables the webhook.
We MUST return 200 for all event types to prevent auto-disable.
"""

import hashlib
import hmac
import logging
import re

from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.config import get_settings
from app.core.dependencies import get_db
from app.core.unified_cache import cache
from app.models.verification import Verification
from app.websocket.manager import manager as websocket_manager

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/verification/webhook", tags=["tv-webhook"])

_DEDUP_TTL = 86400  # 24h


def _verify_signature(payload: bytes, sig_header: str, secret: str) -> bool:
    """Verify TV webhook HMAC-SHA256 signature."""
    if not sig_header:
        return False
    try:
        import base64, hashlib, hmac as _hmac

        raw = secret.replace("whsec_", "") if secret.startswith("whsec_") else secret
        try:
            key = base64.b64decode(raw + "==")
        except Exception:
            key = raw.encode()
        expected = _hmac.new(key, payload, hashlib.sha256).hexdigest()
        received = sig_header.replace("sha256=", "").strip()
        return _hmac.compare_digest(expected, received)
    except Exception as e:
        return False


def _verify_signature(payload: bytes, signature_header: str, secret: str) -> bool:
    """Verify TV webhook HMAC-SHA256 signature.
    TV sends: X-Signature: sha256=<hex_digest>
    """
    if not signature_header or not secret:
        return not secret  # if no secret configured, allow all (dev mode)
    try:
        # Strip whsec_ prefix if present
        raw_secret = (
            secret.replace("whsec_", "") if secret.startswith("whsec_") else secret
        )
        import base64

        secret_bytes = (
            base64.b64decode(raw_secret)
            if len(raw_secret) % 4 == 0
            and all(
                c in "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/="
                for c in raw_secret
            )
            else raw_secret.encode()
        )
        expected = hmac.new(secret_bytes, payload, hashlib.sha256).hexdigest()
        received = signature_header.replace("sha256=", "").strip()
        return hmac.compare_digest(expected, received)
    except Exception as e:
        logger.warning(f"Signature verification error: {e}")
        return False


@router.post("/tv")
async def tv_sms_webhook(request: Request, db: Session = Depends(get_db)):
    """Receive SMS delivery webhooks from TextVerified.

    Payload shape (from SDK WebhookEventSmsWebhookEvent):
    {
        "id": "evt_abc",
        "event": "sms.received",
        "attempt": 1,
        "occurredAt": "...",
        "data": {
            "to": "+17022853600",
            "parsedCode": "876094",
            "smsContent": "Your WhatsApp code is 876-094",
            "reservationId": "tv_verification_id",
            "createdAt": "...",
            "encrypted": false
        }
    }
    """
    try:
        payload = await request.json()
    except Exception:
        # Return 200 anyway — malformed payload shouldn't trigger TV retry/disable
        logger.warning("TV webhook: malformed JSON payload")
        return {"ok": True}

    event_id = payload.get("id", "")
    event_type = payload.get("event", "")

    # Deduplicate — TV retries failed deliveries
    if event_id:
        seen_key = f"tv:webhook:seen:{event_id}"
        if await cache.get(seen_key):
            return {"ok": True, "duplicate": True}
        await cache.set(seen_key, 1, ttl=_DEDUP_TTL)

    # Accept all event types — only process SMS
    if event_type != "sms.received":
        logger.debug(f"TV webhook: ignoring event type '{event_type}'")
        return {"ok": True}

    data = payload.get("data", {})
    reservation_id = data.get("reservationId")  # TV's ID = our activation_id
    phone_number = data.get("to", "")
    sms_content = data.get("smsContent", "")
    parsed_code = data.get("parsedCode", "") or _extract_code(sms_content)

    # Find verification by TV's reservation ID (most reliable)
    verification = None
    if reservation_id:
        verification = (
            db.query(Verification)
            .filter(Verification.activation_id == reservation_id)
            .first()
        )

    # Fallback: match by phone number
    if not verification and phone_number:
        digits = re.sub(r"\D", "", phone_number)[-10:]
        verification = (
            db.query(Verification)
            .filter(
                Verification.phone_number.contains(digits),
                Verification.status == "pending",
            )
            .order_by(Verification.created_at.desc())
            .first()
        )

    if not verification:
        logger.warning(
            f"TV webhook: no verification found for "
            f"reservationId={reservation_id} phone={phone_number}"
        )
        return {"ok": True}  # 200 so TV doesn't retry/disable

    if verification.status != "pending":
        return {"ok": True}  # Already completed

    # Update verification record
    verification.status = "completed"
    verification.sms_code = parsed_code
    verification.sms_text = sms_content
    db.commit()

    logger.info(
        f"TV webhook: SMS delivered — verification={verification.id} "
        f"user={verification.user_id} code={parsed_code}"
    )

    # Push instantly to user's browser via WebSocket
    try:
        await websocket_manager.broadcast_to_user(
            str(verification.user_id),
            {
                "type": "sms_received",
                "verification_id": str(verification.id),
                "sms_code": parsed_code,
                "sms_text": sms_content,
                "phone_number": verification.phone_number,
            },
        )
    except Exception as e:
        logger.warning(f"TV webhook: WebSocket push failed (non-fatal): {e}")

    return {"ok": True}


def _extract_code(text: str) -> str:
    """Fallback code extraction when parsedCode is empty."""
    hyphen = re.findall(r"\b(\d{3}-\d{3})\b", text)
    plain = re.findall(r"\b(\d{4,8})\b", text)
    if hyphen:
        return hyphen[-1].replace("-", "")
    if plain:
        return plain[-1]
    return ""
