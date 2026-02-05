"""Balance synchronization API endpoints."""

from datetime import datetime
from typing import Any, Dict
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.dependencies import get_current_user_id
from app.core.logging import get_logger
from app.models.user import User
from app.models.transaction import Transaction

logger = get_logger(__name__)
router = APIRouter(prefix="/api/balance", tags=["Balance Sync"])


class BalanceSyncService:
    """Service for synchronizing user balances."""

    def __init__(self, db: Session):
        self.db = db

    async def sync_user_balance(self, user: User) -> Dict[str, Any]:
        """Sync user balance with external APIs if applicable."""
        try:
            # Calculate pending transactions
            pending_amount = self.calculate_pending_transactions(user.id)
            
            # Get current database balance
            db_balance = user.credits or 0

            # Only sync with TextVerified API for admin users
            api_balance = None
        if user.is_admin:
                try:
                    api_balance = await self.get_textverified_balance()
                except Exception as e:
                    logger.warning(f"TextVerified balance sync failed: {e}")

            # Calculate available balance
            available_balance = db_balance - pending_amount

            # Update admin balance if API balance is available and different
        if api_balance is not None and abs(db_balance - api_balance) > 0.01:
                user.credits = api_balance
                self.db.commit()
                logger.info(f"Updated admin user {user.id} balance from {db_balance} to {api_balance}")
                db_balance = api_balance

        return {
                "balance": db_balance,
                "available_balance": available_balance,
                "pending_amount": pending_amount,
                "api_balance": api_balance,
                "last_updated": datetime.utcnow().isoformat(),
                "sync_source": "api" if api_balance is not None else "database",
            }

        except Exception as e:
            logger.error(f"Balance sync failed for user {user.id}: {e}")
            raise HTTPException(status_code=500, detail=f"Balance sync failed: {str(e)}")

    async def get_textverified_balance(self) -> float:
        """Get balance from TextVerified API.
        
        This is a placeholder implementation.
        In production, this would make actual API calls.
        """
        try:
            # Placeholder - would make actual API call
            # balance_data = await self.textverified.get_balance()
            # return float(balance_data.get("balance", 0))
        return 0.0
        except Exception as e:
            logger.error(f"TextVerified balance fetch failed: {e}")
            raise

    def calculate_pending_transactions(self, user_id: str) -> float:
        """Calculate pending transaction amounts."""
        try:
            pending_transactions = (
                self.db.query(Transaction)
                .filter(Transaction.user_id == user_id, Transaction.status == "pending")
                .all()
            )

        return sum(abs(t.amount) for t in pending_transactions if t.amount < 0)
        except Exception as e:
            logger.error(f"Pending transactions calculation failed: {e}")
        return 0.0


        @router.get("/sync")
    async def sync_balance(
        user_id: str = Depends(get_current_user_id),
        db: Session = Depends(get_db)
        ) -> Dict[str, Any]:
        """Sync user balance with external APIs."""
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
        raise HTTPException(status_code=404, detail="User not found")

        balance_service = BalanceSyncService(db)
        return await balance_service.sync_user_balance(user)


        @router.get("/real-time")
    async def get_real_time_balance(
        user_id: str = Depends(get_current_user_id),
        db: Session = Depends(get_db)
        ) -> Dict[str, Any]:
        """Get real-time balance information."""
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
        raise HTTPException(status_code=404, detail="User not found")

        try:
        # Get current balance
        current_balance = user.credits or 0
        
        # Calculate pending amount
        balance_service = BalanceSyncService(db)
        pending_amount = balance_service.calculate_pending_transactions(user.id)
        
        # Calculate available balance
        available_balance = current_balance - pending_amount

        return {
            "balance": current_balance,
            "available_balance": available_balance,
            "pending_amount": pending_amount,
            "last_updated": datetime.utcnow().isoformat(),
        }

        except Exception as e:
        logger.error(f"Real-time balance fetch failed for user {user.id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to get real-time balance")


        @router.post("/refresh")
    async def refresh_balance(
        user_id: str = Depends(get_current_user_id),
        db: Session = Depends(get_db)
        ) -> Dict[str, Any]:
        """Force refresh user balance from all sources."""
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
        raise HTTPException(status_code=404, detail="User not found")

        balance_service = BalanceSyncService(db)
        result = await balance_service.sync_user_balance(user)
    
        logger.info(f"Balance refreshed for user {user.id}")
        return result
