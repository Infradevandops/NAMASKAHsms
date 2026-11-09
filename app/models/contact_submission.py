"""ContactSubmission model — durable storage for contact form submissions."""

from sqlalchemy import Column, String, Text

from app.models.base import BaseModel


class ContactSubmission(BaseModel):
    """
    Persists every contact form submission before acknowledging receipt.

    Forwarding to support is a downstream action; the submission is durable
    regardless of whether the email provider is reachable.
    """

    __tablename__ = "contact_submissions"

    name = Column(String(100), nullable=False)
    email = Column(String(255), nullable=False, index=True)
    subject = Column(String(200), nullable=False)
    category = Column(String(50), nullable=False, default="support")
    message = Column(Text, nullable=False)
    # forwarding_status: pending | sent | failed
    forwarding_status = Column(String(20), nullable=False, default="pending")
    forwarding_error = Column(Text, nullable=True)
