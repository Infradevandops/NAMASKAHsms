"""Admin user management endpoints."""

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user_id
from app.models.user import User

router = APIRouter()


async def require_admin(
    user_id: str = Depends(get_current_user_id), db: Session = Depends(get_db)
):
    """Verify admin access."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user or not user.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")
    return user_id


@router.get("/users/list")
async def list_users(
    admin_id: str = Depends(require_admin),
    db: Session = Depends(get_db),
    limit: int = 50,
    offset: int = 0,
):
    """List users with pagination."""
    try:
        users = db.query(User).limit(limit).offset(offset).all()
        total = db.query(User).count()
        return {
            "users": [
                {
                    "id": u.id,
                    "email": u.email,
                    "tier": getattr(u, "tier", "freemium"),
                    "credits": float(u.credits or 0.0),
                    "is_admin": u.is_admin,
                    "created_at": u.created_at.isoformat() if u.created_at else None,
                }
                for u in users
            ],
            "total": total,
            "limit": limit,
            "offset": offset,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list users: {str(e)}")


@router.get("/users")
async def get_users(
    admin_id: str = Depends(require_admin),
    db: Session = Depends(get_db),
    limit: int = 50,
    offset: int = 0,
):
    """Alias for list_users."""
    return await list_users(admin_id, db, limit, offset)


@router.post("/users/{user_id}/approve-affiliate")
async def approve_affiliate(
    user_id: str,
    admin_id: str = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Approve a user as an affiliate partner."""
    from app.services.audit_service import AuditService

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if user.is_affiliate:
        return {"status": "already_affiliate", "user_id": user_id}

    user.is_affiliate = True
    user.partner_type = "affiliate"
    user.commission_tier = "starter"
    db.commit()

    try:
        import asyncio

        asyncio.create_task(
            AuditService(db).log_action(
                user_id=admin_id,
                action="affiliate_approved",
                resource_type="user",
                resource_id=user_id,
                details={"commission_tier": "starter"},
            )
        )
    except Exception:
        pass

    return {"status": "approved", "user_id": user_id, "commission_tier": "starter"}


@router.post("/users/{user_id}/revoke-affiliate")
async def revoke_affiliate(
    user_id: str,
    admin_id: str = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Revoke affiliate status from a user."""
    from app.services.audit_service import AuditService

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user.is_affiliate = False
    user.partner_type = None
    user.commission_tier = None
    db.commit()

    try:
        import asyncio

        asyncio.create_task(
            AuditService(db).log_action(
                user_id=admin_id,
                action="affiliate_revoked",
                resource_type="user",
                resource_id=user_id,
            )
        )
    except Exception:
        pass

    return {"status": "revoked", "user_id": user_id}


@router.get("/users/{user_id}")
async def get_user_details(
    user_id: str,
    admin_id: str = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Get detailed user information."""
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        return {
            "id": user.id,
            "email": user.email,
            "tier": getattr(user, "subscription_tier", "freemium") or "freemium",
            "credits": float(user.credits or 0.0),
            "is_admin": user.is_admin,
            "is_affiliate": getattr(user, "is_affiliate", False),
            "partner_type": getattr(user, "partner_type", None),
            "commission_tier": getattr(user, "commission_tier", None),
            "created_at": user.created_at.isoformat() if user.created_at else None,
            "last_login": getattr(user, "last_login", None),
            "is_suspended": getattr(user, "is_suspended", False),
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get user: {str(e)}")


@router.put("/users/{user_id}/tier")
async def update_user_tier(
    user_id: str,
    tier: str,
    admin_id: str = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Update user's subscription tier."""
    from app.services.audit_service import AuditService

    try:
        valid_tiers = ["freemium", "payg", "pro", "custom", "enterprise"]
        if tier not in valid_tiers:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid tier. Must be one of: {', '.join(valid_tiers)}",
            )

        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        old_tier = getattr(user, "subscription_tier", "freemium")
        user.subscription_tier = tier
        db.commit()

        try:
            import asyncio

            asyncio.create_task(
                AuditService(db).log_action(
                    user_id=admin_id,
                    action="tier_updated",
                    resource_type="user",
                    resource_id=user_id,
                    details={"old_tier": old_tier, "new_tier": tier},
                )
            )
        except Exception:
            pass

        return {
            "status": "success",
            "user_id": user_id,
            "old_tier": old_tier,
            "new_tier": tier,
        }
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to update tier: {str(e)}")


@router.put("/users/{user_id}/credits")
async def adjust_user_credits(
    user_id: str,
    action: str,
    amount: float,
    reason: str = "",
    admin_id: str = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Adjust user credits (add, deduct, or set)."""
    from app.services.audit_service import AuditService

    try:
        valid_actions = ["add", "deduct", "set"]
        if action not in valid_actions:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid action. Must be one of: {', '.join(valid_actions)}",
            )

        if amount < 0:
            raise HTTPException(status_code=400, detail="Amount must be positive")

        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        old_credits = float(user.credits or 0.0)
        new_credits = old_credits

        if action == "add":
            new_credits = old_credits + amount
        elif action == "deduct":
            new_credits = max(0, old_credits - amount)
        elif action == "set":
            new_credits = amount

        user.credits = new_credits
        db.commit()

        try:
            import asyncio

            asyncio.create_task(
                AuditService(db).log_action(
                    user_id=admin_id,
                    action="credits_adjusted",
                    resource_type="user",
                    resource_id=user_id,
                    details={
                        "action": action,
                        "amount": amount,
                        "old_credits": old_credits,
                        "new_credits": new_credits,
                        "reason": reason,
                    },
                )
            )
        except Exception:
            pass

        return {
            "status": "success",
            "user_id": user_id,
            "action": action,
            "old_credits": old_credits,
            "new_credits": new_credits,
        }
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500, detail=f"Failed to adjust credits: {str(e)}"
        )


@router.post("/users/{user_id}/suspend")
async def suspend_user(
    user_id: str,
    reason: str = "",
    admin_id: str = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Suspend a user account."""
    from app.services.audit_service import AuditService

    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        if user.is_admin:
            raise HTTPException(status_code=403, detail="Cannot suspend admin users")

        # Add is_suspended field if it doesn't exist
        if not hasattr(user, "is_suspended"):
            from sqlalchemy import Boolean, Column

            # For now, we'll use a workaround
            pass

        user.is_suspended = True
        db.commit()

        try:
            import asyncio

            asyncio.create_task(
                AuditService(db).log_action(
                    user_id=admin_id,
                    action="user_suspended",
                    resource_type="user",
                    resource_id=user_id,
                    details={"reason": reason},
                )
            )
        except Exception:
            pass

        return {"status": "suspended", "user_id": user_id}
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to suspend user: {str(e)}")


@router.post("/users/{user_id}/activate")
async def activate_user(
    user_id: str,
    admin_id: str = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Activate a suspended user account."""
    from app.services.audit_service import AuditService

    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        user.is_suspended = False
        db.commit()

        try:
            import asyncio

            asyncio.create_task(
                AuditService(db).log_action(
                    user_id=admin_id,
                    action="user_activated",
                    resource_type="user",
                    resource_id=user_id,
                )
            )
        except Exception:
            pass

        return {"status": "activated", "user_id": user_id}
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500, detail=f"Failed to activate user: {str(e)}"
        )
