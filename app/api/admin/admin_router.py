"""Admin endpoints with RBAC."""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.rbac import require_admin, require_moderator_or_admin, get_user_role
from app.models.user import User
from app.schemas import SuccessResponse

router = APIRouter(prefix="/admin", tags=["Admin"])


@router.get("/users")
async def list_users(
    user_id: str = Depends(require_admin),
    db: Session = Depends(get_db)
):
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
                "created_at": u.created_at
            }
            for u in users
        ]
    }


@router.post("/users/{user_id}/promote-moderator")
async def promote_to_moderator(
    user_id: str,
    admin_id: str = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Promote user to moderator (admin only)."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        return {"error": "User not found"}

    user.is_moderator = True
    db.commit()
    return SuccessResponse(message=f"User {user.email} promoted to moderator")


@router.post("/users/{user_id}/promote-admin")
async def promote_to_admin(
    user_id: str,
    admin_id: str = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Promote user to admin (admin only)."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        return {"error": "User not found"}

    user.is_admin = True
    db.commit()
    return SuccessResponse(message=f"User {user.email} promoted to admin")


@router.post("/users/{user_id}/demote")
async def demote_user(
    user_id: str,
    admin_id: str = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Demote user to regular user (admin only)."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        return {"error": "User not found"}

    user.is_admin = False
    user.is_moderator = False
    db.commit()
    return SuccessResponse(message=f"User {user.email} demoted to regular user")


@router.get("/stats")
async def get_stats(
    user_id: str = Depends(require_moderator_or_admin),
    db: Session = Depends(get_db)
):
    """Get system statistics (moderator or admin)."""
    total_users = db.query(User).count()
    admin_users = db.query(User).filter(User.is_admin).count()
    moderator_users = db.query(User).filter(User.is_moderator).count()

    return {
        "total_users": total_users,
        "admin_users": admin_users,
        "moderator_users": moderator_users,
        "regular_users": total_users - admin_users - moderator_users
    }
