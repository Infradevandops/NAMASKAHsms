"""Personal phone number model for custom verification."""

from sqlalchemy import Boolean, Column, ForeignKey, String
from sqlalchemy.orm import relationship

from app.models.base import BaseModel


class PersonalNumber(BaseModel):
    __tablename__ = "personal_numbers"

    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    phone_number = Column(String(20), nullable=False)
    country_code = Column(String(5), nullable=False)
    is_verified = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)

    # Relationships
    user = relationship("User", back_populates="personal_numbers")
