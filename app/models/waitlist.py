"""Waitlist model for pre-launch email collection."""
from sqlalchemy import Column, String, Boolean
from app.models.base import BaseModel

class Waitlist(BaseModel):
    __tablename__ = "waitlist"
    
    email = Column(String(255), nullable=False, unique=True, index=True)
    name = Column(String(100), nullable=True)
    is_notified = Column(Boolean, default=False)
    source = Column(String(50), default="landing_page")