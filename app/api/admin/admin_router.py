"""Admin endpoints with RBAC."""


from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.dependencies import get_current_user_id
from app.core.logging import get_logger
from app.core.tier_config import TierConfig
from app.models.user import User

logger = get_logger(__name__)


class SuccessResponse(BaseModel):

    message: str


    async def require_admin(user_id: str = Depends(get_current_user_id), db: Session = Depends(get_db)):
        user = db.query(User).filter(User.id == user_id).first()
        if not user or not user.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")
        return user_id


    async def require_moderator_or_admin(user_id: str = Depends(get_current_user_id), db: Session = Depends(get_db)):
        user = db.query(User).filter(User.id == user_id).first()
        if not user or (not user.is_admin and not user.is_moderator):
        raise HTTPException(status_code=403, detail="Moderator or admin access required")
        return user_id


    def get_user_role(db, user_id):
    class Role:
        value = "user"
        return Role()


        router = APIRouter(prefix="/admin", tags=["Admin"])


        @router.get("/users")
    async def list_users(user_id: str = Depends(require_admin), db: Session = Depends(get_db)):
        """List all users (admin only)."""
        users = db.query(User).all()
        return {
        "total": len(users),
        "users": [
            {
                "id": u.id,
                "email": u.email,
                "role": get_user_role(db, u.id).value,
                "credits": u.credits,
                "created_at": u.created_at,
            }
            for u in users
        ],
        }


        @router.post("/users/{user_id}/promote-moderator")
    async def promote_to_moderator(user_id: str, admin_id: str = Depends(require_admin), db: Session = Depends(get_db)):
        """Promote user to moderator (admin only)."""
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
        return {"error": "User not found"}

        user.is_moderator = True
        db.commit()
        return SuccessResponse(message=f"User {user.email} promoted to moderator")


        @router.post("/users/{user_id}/promote-admin")
    async def promote_to_admin(user_id: str, admin_id: str = Depends(require_admin), db: Session = Depends(get_db)):
        """Promote user to admin (admin only)."""
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
        return {"error": "User not found"}

        user.is_admin = True
        db.commit()
        return SuccessResponse(message=f"User {user.email} promoted to admin")


        @router.post("/users/{user_id}/demote")
    async def demote_user(user_id: str, admin_id: str = Depends(require_admin), db: Session = Depends(get_db)):
        """Demote user to regular user (admin only)."""
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
        return {"error": "User not found"}

        user.is_admin = False
        user.is_moderator = False
        db.commit()
        return SuccessResponse(message=f"User {user.email} demoted to regular user")


        @router.get("/stats")
    async def get_stats(user_id: str = Depends(require_moderator_or_admin), db: Session = Depends(get_db)):
        """Get system statistics (moderator or admin)."""
        total_users = db.query(User).count()
        admin_users = db.query(User).filter(User.is_admin).count()
        moderator_users = db.query(User).filter(User.is_moderator).count()

        return {
        "total_users": total_users,
        "admin_users": admin_users,
        "moderator_users": moderator_users,
        "regular_users": total_users - admin_users - moderator_users,
        }


class SetUserTierRequest(BaseModel):

        tier: str
        duration_days: int = 30


        @router.post("/users/{user_id}/tier")
    async def set_user_tier(
        user_id: str,
        request: SetUserTierRequest,
        admin_id: str = Depends(require_admin),
        db: Session = Depends(get_db),
        ):
        """Set user tier directly (admin only)."""
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
        raise HTTPException(status_code=404, detail="User not found")

        valid_tiers = ["freemium", "payg", "pro", "custom"]
        if request.tier not in valid_tiers:
        raise HTTPException(status_code=400, detail=f"Invalid tier. Must be one of: {valid_tiers}")

        old_tier = user.subscription_tier or "payg"
        user.subscription_tier = request.tier

        if request.tier != "payg":
        user.tier_expires_at = datetime.now(timezone.utc) + timedelta(days=request.duration_days)
        else:
        user.tier_expires_at = None

        db.commit()
        logger.info(f"Admin {admin_id} changed user {user_id} tier from {old_tier} to {request.tier}")

        return {
        "success": True,
        "message": f"User tier updated from {old_tier} to {request.tier}",
        "user_id": user_id,
        "new_tier": request.tier,
        "expires_at": user.tier_expires_at,
        }


        @router.get("/users/{user_id}/tier")
    async def get_user_tier(user_id: str, admin_id: str = Depends(require_admin), db: Session = Depends(get_db)):
        """Get user's current tier info (admin only)."""
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
        raise HTTPException(status_code=404, detail="User not found")

        tier = user.subscription_tier or "payg"
        tier_config = TierConfig.get_tier_config(tier, db)

        return {
        "user_id": user_id,
        "email": user.email,
        "current_tier": tier,
        "tier_name": tier_config["name"],
        "expires_at": user.tier_expires_at,
        "tier_config": {
            "price_monthly": tier_config["price_monthly"],
            "quota_usd": tier_config["quota_usd"],
            "api_key_limit": tier_config["api_key_limit"],
            "has_api_access": tier_config["has_api_access"],
            "has_area_code_selection": tier_config["has_area_code_selection"],
            "has_isp_filtering": tier_config["has_isp_filtering"],
        },
        }
