from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.user import User
from app.models.verification import Verification
from app.api.admin.dependencies import require_admin
from datetime import datetime

router = APIRouter(prefix="/api/admin", tags=["admin-actions"])

@router.post("/users/{user_id}/suspend")
async def suspend_user(
    user_id: str,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Suspend a user account"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    user.is_active = False
    db.commit()
    
    return {"success": True, "message": f"User {user.email} suspended"}

@router.post("/users/{user_id}/activate")
async def activate_user(
    user_id: str,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Activate a user account"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    user.is_active = True
    db.commit()
    
    return {"success": True, "message": f"User {user.email} activated"}

@router.post("/verifications/{verification_id}/cancel")
async def cancel_verification(
    verification_id: str,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Cancel a pending verification"""
    verification = db.query(Verification).filter(Verification.id == verification_id).first()
    if not verification:
        raise HTTPException(status_code=404, detail="Verification not found")
    
    verification.status = "cancelled"
    verification.updated_at = datetime.now()
    db.commit()
    
    return {"success": True, "message": "Verification cancelled"}

@router.get("/users/list")
async def list_users(
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
    limit: int = 50,
    offset: int = 0
):
    """Get list of users for admin management"""
    users = db.query(User).offset(offset).limit(limit).all()
    
    return [
        {
            "id": user.id,
            "email": user.email,
            "is_admin": user.is_admin,
            "is_active": user.is_active,
            "credits": float(user.credits or 0),
            "tier": user.tier or "freemium",
            "created_at": user.created_at.isoformat() if user.created_at else "",
            "last_login": user.last_login.isoformat() if hasattr(user, 'last_login') and user.last_login else ""
        }
        for user in users
    ]

@router.post("/export/verifications")
async def export_verifications(
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Export verification data"""
    verifications = db.query(Verification).all()
    
    return {
        "success": True,
        "message": f"Exported {len(verifications)} verifications",
        "download_url": "/api/admin/download/verifications.csv"
    }

@router.post("/export/users")
async def export_users(
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Export user data"""
    users = db.query(User).all()
    
    return {
        "success": True,
        "message": f"Exported {len(users)} users",
        "download_url": "/api/admin/download/users.csv"
    }