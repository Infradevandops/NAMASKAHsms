"""Balance transaction model for tracking balance changes."""


from sqlalchemy import Column, ForeignKey, Numeric, String, Text
from sqlalchemy.orm import relationship
from app.models.base import BaseModel

class BalanceTransaction(BaseModel):

    """Balance transaction model."""

    __tablename__ = "balance_transactions"

    user_id = Column(String, ForeignKey("users.id"), nullable=False, index=True)
    amount = Column(Numeric(10, 2), nullable=False)
    type = Column(String(50), nullable=False)  # credit, debit, refund
    description = Column(Text)
    balance_after = Column(Numeric(10, 2), nullable=False)

    # Relationship
    user = relationship("User", back_populates="balance_transactions")

    def to_dict(self):

        """Convert to dictionary."""
        return {
            "id": self.id,
            "amount": float(self.amount),
            "type": self.type,
            "description": self.description,
            "balance_after": float(self.balance_after),
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
