from pydantic import BaseModel
from datetime import datetime

class TierAccessDenied(BaseModel):
    message: str
    current_tier: str
    required_tier: str
    upgrade_url: str = "/billing/upgrade"
    timestamp: datetime
