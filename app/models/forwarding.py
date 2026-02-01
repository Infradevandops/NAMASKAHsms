"""SMS forwarding configuration model."""


from sqlalchemy import JSON, Boolean, Column, String
from app.models.base import BaseModel

class ForwardingConfig(BaseModel):

    """SMS forwarding configuration."""

    __tablename__ = "forwarding_config"

    user_id = Column(String, nullable=False, index=True, unique=True)

    # Email forwarding
    email_enabled = Column(Boolean, default=False)
    email_address = Column(String)

    # Webhook forwarding
    webhook_enabled = Column(Boolean, default=False)
    webhook_url = Column(String)
    webhook_secret = Column(String)

    # Additional settings
    forward_all = Column(Boolean, default=True)
    forward_services = Column(JSON)  # List of services to forward

    # Status
    is_active = Column(Boolean, default=True)
