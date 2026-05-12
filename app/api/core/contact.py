"""Contact form endpoint."""

from fastapi import APIRouter
from pydantic import BaseModel, EmailStr, Field

from app.core.logging import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/api/contact", tags=["Contact"])


class ContactRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    email: EmailStr
    subject: str = Field(..., min_length=1, max_length=200)
    category: str = Field(default="support")
    message: str = Field(..., min_length=10, max_length=5000)


@router.post("/send")
async def send_contact_message(data: ContactRequest):
    """Receive contact form submission."""
    try:
        logger.info(f"Contact form: {data.category} from {data.email} - {data.subject}")

        # In production, integrate with email service or ticketing system
        # For now, log and acknowledge
        try:
            from app.services.email_service import email_service

            await email_service.send_email(
                to_email="support@namaskah.app",
                subject=f"[Contact Form] {data.category}: {data.subject}",
                html_content=f"""
                <h3>New Contact Form Submission</h3>
                <p><strong>From:</strong> {data.name} ({data.email})</p>
                <p><strong>Category:</strong> {data.category}</p>
                <p><strong>Subject:</strong> {data.subject}</p>
                <hr>
                <p>{data.message}</p>
                """,
            )
        except Exception as e:
            logger.warning(f"Failed to forward contact email: {e}")

        return {
            "status": "success",
            "message": "Message received. We'll respond within 24 hours.",
        }
    except Exception as e:
        logger.error(f"Error processing contact form: {e}", exc_info=True)
        from fastapi import HTTPException

        raise HTTPException(status_code=500, detail="Failed to send message")
