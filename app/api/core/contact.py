"""Contact form endpoint — persists submission before acknowledging, then forwards."""

import html

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.logging import get_logger
from app.models.contact_submission import ContactSubmission

logger = get_logger(__name__)
router = APIRouter(prefix="/api/contact", tags=["Contact"])


class ContactRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    email: EmailStr
    subject: str = Field(..., min_length=1, max_length=200)
    category: str = Field(default="support")
    message: str = Field(..., min_length=10, max_length=5000)


@router.post("/send")
async def send_contact_message(data: ContactRequest, db: Session = Depends(get_db)):
    """
    Receive contact form submission.

    Persists to DB first — success response only after durable write.
    Support forwarding is best-effort; failure is logged and retryable.
    """
    # 1. Persist submission (durable — never lose the message)
    submission = ContactSubmission(
        name=data.name,
        email=str(data.email),
        subject=data.subject,
        category=data.category,
        message=data.message,
        forwarding_status="pending",
    )
    db.add(submission)
    db.commit()
    db.refresh(submission)

    logger.info(
        f"Contact submission {submission.id} persisted: "
        f"category={data.category} from={data.email}"
    )

    # 2. Attempt forwarding to support (best-effort, non-blocking)
    try:
        from app.core.config import get_settings
        from app.services.email_service import email_service

        settings = get_settings()
        support_dest = settings.support_email or "support@vrenum.app"

        # Escape all user-provided content before interpolating into HTML
        safe_name = html.escape(data.name)
        safe_email = html.escape(str(data.email))
        safe_category = html.escape(data.category)
        safe_subject = html.escape(data.subject)
        safe_message = html.escape(data.message).replace("\n", "<br>")

        forwarding_html = (
            "<h3>New Contact Form Submission</h3>"
            f"<p><strong>Submission ID:</strong> {submission.id}</p>"
            f"<p><strong>From:</strong> {safe_name} ({safe_email})</p>"
            f"<p><strong>Category:</strong> {safe_category}</p>"
            f"<p><strong>Subject:</strong> {safe_subject}</p>"
            "<hr>"
            f"<p>{safe_message}</p>"
        )

        sent = await email_service._send(
            support_dest,
            f"[Contact Form] {data.category}: {data.subject}",
            forwarding_html,
        )

        submission.forwarding_status = "sent" if sent else "failed"
        if not sent:
            submission.forwarding_error = "email_service returned False"
        db.commit()

    except Exception as exc:
        logger.warning(f"Contact forwarding failed for {submission.id}: {exc}")
        try:
            submission.forwarding_status = "failed"
            submission.forwarding_error = str(exc)[:500]
            db.commit()
        except Exception:
            pass

    return {
        "status": "success",
        "message": "Message received. We'll respond within 24 hours.",
        "submission_id": submission.id,
    }
