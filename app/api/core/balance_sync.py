"""
import logging
from datetime import datetime
from typing import Any, Dict
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.transaction import Transaction
from app.models.user import User
from app.services.textverified_service import TextVerifiedService

Real-time Balance Sync Service
Handles live balance updates and synchronization
"""


logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/balance", tags=["balance"])


class BalanceSyncService:

    def __init__(self, db: Session):

        self.db = db
        self.textverified = TextVerifiedService()

    async def sync_user_balance(self, user: User) -> Dict[str, Any]:
        """
        Sync user balance with real-time data
        """
        try:
            # Get current database balance
            db_balance = user.credits or 0

            # Only sync with TextVerified API for admin users
            api_balance = None
        if user.is_admin:
        try:
                    api_balance = await self.get_textverified_balance()
        except Exception as e:
                    logger.warning(f"TextVerified balance sync failed: {e}")

            # Calculate pending transactions
            pending_amount = self.calculate_pending_transactions(user.id)

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
        """
        Get balance from TextVerified API
        """
        try:
            balance_data = await self.textverified.get_balance()
        return float(balance_data.get("balance", 0))
        except Exception as e:
            logger.error(f"TextVerified balance fetch failed: {e}")
            raise

    def calculate_pending_transactions(self, user_id: int) -> float:

        """
        Calculate pending transaction amounts
        """
        try:
            pending_transactions = (
                self.db.query(Transaction).filter(Transaction.user_id == user_id, Transaction.status == "pending").all()
            )

        return sum(abs(t.amount) for t in pending_transactions if t.amount < 0)
        except Exception as e:
            logger.error(f"Pending transactions calculation failed: {e}")
        return 0.0


        @router.get("/sync")
    async def sync_balance(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> Dict[str, Any]:
        """
        Sync user balance with real-time data
        """
        sync_service = BalanceSyncService(db)
        return await sync_service.sync_user_balance(current_user)


        @router.get("/real-time")
    async def get_real_time_balance(
        current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
        ) -> Dict[str, Any]:
        """
        Get real-time balance - TextVerified API balance only for admins
        """
        try:
        # Admin users get TextVerified API balance, regular users get their individual balance
        if current_user.is_admin:
            tv_service = TextVerifiedService()
        if tv_service.enabled:
        try:
                    balance_data = await tv_service.get_balance()
                    api_balance = float(balance_data.get("balance", 0))

                    # Update admin's database balance
        if abs((current_user.credits or 0) - api_balance) > 0.01:
                        current_user.credits = api_balance
                        db.commit()
                        logger.info(f"Admin balance synced: ${api_balance:.2f}")

        return {
                        "balance": api_balance,
                        "formatted_balance": f"${api_balance:.2f}",
                        "last_updated": datetime.utcnow().isoformat(),
                        "source": "textverified_api",
                        "cache_disabled": True,
                    }
        except Exception as e:
                    logger.warning(f"TextVerified API failed for admin: {e}")

        # Regular users or API failure - use database balance
        balance = current_user.credits or 0

        return {
            "balance": balance,
            "formatted_balance": f"${balance:.2f}",
            "last_updated": datetime.utcnow().isoformat(),
            "source": "database",
            "cache_disabled": True,
        }

        except Exception as e:
        logger.error(f"Real-time balance fetch failed: {e}")
        raise HTTPException(status_code=500, detail=f"Balance fetch failed: {str(e)}")


        @router.post("/refresh")
    async def force_balance_refresh(
        current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
        ) -> Dict[str, Any]:
        """
        Force refresh balance from all sources
        """
        try:
        sync_service = BalanceSyncService(db)
        result = await sync_service.sync_user_balance(current_user)

        return {
            "message": "Balance refreshed successfully",
            "data": result,
            "refreshed_at": datetime.utcnow().isoformat(),
        }

        except Exception as e:
        logger.error(f"Force balance refresh failed: {e}")
        raise HTTPException(status_code=500, detail=f"Balance refresh failed: {str(e)}")


        @router.get("/tier-info")
    async def get_tier_info(
        current_user: User = Depends(get_current_user),
        ) -> Dict[str, Any]:
        """
        Get real-time tier information
        """
        try:
        tier = current_user.subscription_tier or "freemium"

        # Tier display mapping
        tier_display = {
            "freemium": "FREEMIUM",
            "payg": "PAY-AS-YOU-GO",
            "starter": "STARTER",
            "pro": "PRO",
            "turbo": "TURBO",
            "custom": "CUSTOM",
        }

        return {
            "subscription_tier": tier,
            "tier_name": tier_display.get(tier, tier.upper()),
            "tier_display": tier_display.get(tier, tier.upper()),
            "is_admin": current_user.is_admin,
            "last_updated": datetime.utcnow().isoformat(),
        }

        except Exception as e:
        logger.error(f"Tier info fetch failed: {e}")
        raise HTTPException(status_code=500, detail=f"Tier info failed: {str(e)}")