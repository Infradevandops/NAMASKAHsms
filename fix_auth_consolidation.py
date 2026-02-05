#!/usr/bin/env python3
"""
Consolidate and fix the scattered authentication system.
"""

import os
import sys
from pathlib import Path

def main():
    """Fix the authentication system."""
    
    print("🔧 Consolidating Authentication System...")
    
    # 1. Disable conflicting core router
    core_router_path = Path("app/api/core/router.py")
    if core_router_path.exists():
        content = core_router_path.read_text()
        # Comment out the auth router inclusion
        content = content.replace(
            "router.include_router(auth_router, prefix=\"/api\")",
            "# router.include_router(auth_router, prefix=\"/api\")  # Disabled - using auth_standalone"
        )
        core_router_path.write_text(content)
        print("✅ Disabled conflicting core auth router")
    
    # 2. Create a clean, consolidated auth router
    auth_consolidated_path = Path("app/api/auth_consolidated.py")
    auth_consolidated_content = '''"""
Consolidated Authentication System - Single Source of Truth
"""

from datetime import datetime, timedelta
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session
import bcrypt
import jwt

from app.core.config import get_settings
from app.core.database import get_db
from app.core.logging import get_logger
from app.models.user import User

logger = get_logger(__name__)
router = APIRouter(prefix="/api/auth", tags=["Authentication"])
security = HTTPBearer()
settings = get_settings()


class LoginRequest(BaseModel):
    """Login request model."""
    email: EmailStr
    password: str


class RegisterRequest(BaseModel):
    """Register request model."""
    email: EmailStr
    password: str
    username: Optional[str] = None


class TokenResponse(BaseModel):
    """Token response model."""
    access_token: str
    token_type: str = "bearer"
    user: dict


@router.post("/login", response_model=TokenResponse)
    async def login(login_data: LoginRequest, db: Session = Depends(get_db)):
        """Login endpoint - consolidated and working."""
        try:
        # Find user by email
        user = db.query(User).filter(User.email == login_data.email).first()
        
        if not user:
            logger.warning(f"Login attempt with non-existent email: {login_data.email}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password"
            )
        
        # Verify password
        if not user.password_hash:
            logger.error(f"User {user.email} has no password hash")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password"
            )
            
        if not bcrypt.checkpw(
            login_data.password.encode('utf-8'),
            user.password_hash.encode('utf-8')
        ):
            logger.warning(f"Invalid password for user: {user.email}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password"
            )
        
        # Check if user is active
        if not user.is_active:
            logger.warning(f"Login attempt for inactive user: {user.email}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Account is disabled"
            )
        
        # Generate JWT token
        token_data = {
            "user_id": str(user.id),
            "email": user.email,
            "exp": datetime.utcnow() + timedelta(days=7)
        }
        
        access_token = jwt.encode(
            token_data,
            settings.jwt_secret_key,
            algorithm=settings.jwt_algorithm
        )
        
        # Update last login
        user.last_login = datetime.utcnow()
        db.commit()
        
        logger.info(f"Successful login: {user.email}")
        
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user": {
                "id": str(user.id),
                "email": user.email,
                "username": user.username,
                "credits": float(user.credits) if user.credits else 0.0,
                "is_active": user.is_active,
            }
        }
        
        except HTTPException:
        raise
        except Exception as e:
        logger.error(f"Login error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Login failed"
        )


        @router.post("/register", response_model=TokenResponse)
    async def register(register_data: RegisterRequest, db: Session = Depends(get_db)):
        """Register endpoint - consolidated and working."""
        try:
        # Check if user already exists
        existing_user = db.query(User).filter(User.email == register_data.email).first()
        
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
        
        # Hash password
        password_hash = bcrypt.hashpw(
            register_data.password.encode('utf-8'),
            bcrypt.gensalt()
        ).decode('utf-8')
        
        # Create user
        user = User(
            email=register_data.email,
            username=register_data.username or register_data.email.split('@')[0],
            password_hash=password_hash,
            is_active=True,
            credits=0.0,
            created_at=datetime.utcnow()
        )
        
        db.add(user)
        db.commit()
        db.refresh(user)
        
        # Generate JWT token
        token_data = {
            "user_id": str(user.id),
            "email": user.email,
            "exp": datetime.utcnow() + timedelta(days=7)
        }
        
        access_token = jwt.encode(
            token_data,
            settings.jwt_secret_key,
            algorithm=settings.jwt_algorithm
        )
        
        logger.info(f"New user registered: {user.email}")
        
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user": {
                "id": str(user.id),
                "email": user.email,
                "username": user.username,
                "credits": 0.0,
                "is_active": True,
            }
        }
        
        except HTTPException:
        raise
        except Exception as e:
        logger.error(f"Registration error: {str(e)}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Registration failed"
        )


        @router.get("/me")
    async def get_current_user(
        credentials: HTTPAuthorizationCredentials = Depends(security),
        db: Session = Depends(get_db)
        ):
        """Get current user info."""
        try:
        # Decode token
        payload = jwt.decode(
            credentials.credentials,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm]
        )
        
        user_id = payload.get("user_id")
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token"
            )
        
        # Get user
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        return {
            "id": str(user.id),
            "email": user.email,
            "username": user.username,
            "credits": float(user.credits) if user.credits else 0.0,
            "is_active": user.is_active,
        }
        
        except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token expired"
        )
        except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )
        except Exception as e:
        logger.error(f"Get user error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get user info"
        )


        @router.post("/logout")
    async def logout():
        """Logout endpoint (client should discard token)."""
        return {"message": "Successfully logged out"}
        '''
    
        auth_consolidated_path.write_text(auth_consolidated_content)
        print("✅ Created consolidated auth router")
    
    # 3. Update main.py to use the consolidated auth
        main_py_path = Path("main.py")
        if main_py_path.exists():
        content = main_py_path.read_text()
        
        # Replace the import
        content = content.replace(
            "from app.api.auth_standalone import router as auth_router",
            "from app.api.auth_consolidated import router as auth_router"
        )
        
        main_py_path.write_text(content)
        print("✅ Updated main.py to use consolidated auth")
    
    # 4. Fix User model relationships
        user_model_path = Path("app/models/user.py")
        if user_model_path.exists():
        content = user_model_path.read_text()
        
        # Remove problematic relationships that cause circular imports
        problematic_relationships = [
            'activities = relationship("Activity", back_populates="user")',
            'activities: Mapped[List["Activity"]] = relationship(back_populates="user")',
        ]
        
        for rel in problematic_relationships:
        if rel in content:
                content = content.replace(rel, f"# {rel}  # Disabled to fix circular import")
        
        user_model_path.write_text(content)
        print("✅ Fixed User model relationships")
    
    # 5. Create a test admin user
        create_test_user_script = '''#!/usr/bin/env python3
        """Create test admin user."""

        import sys
        from pathlib import Path
        sys.path.append(str(Path(__file__).parent))

        from app.core.database import get_db
        from app.models.user import User
        import bcrypt
        from datetime import datetime

    def create_admin():
        """Create admin user."""
        try:
        db = next(get_db())
        
        # Check if admin exists
        admin = db.query(User).filter(User.email == "admin@namaskah.app").first()
        if admin:
            print("Admin user already exists")
            return
        
        # Create admin
        password_hash = bcrypt.hashpw(
            "admin123".encode('utf-8'),
            bcrypt.gensalt()
        ).decode('utf-8')
        
        admin = User(
            email="admin@namaskah.app",
            username="admin",
            password_hash=password_hash,
            is_active=True,
            credits=1000.0,
            created_at=datetime.utcnow()
        )
        
        db.add(admin)
        db.commit()
        
        print("✅ Admin user created:")
        print("   Email: admin@namaskah.app")
        print("   Password: admin123")
        
        except Exception as e:
        print(f"❌ Error creating admin: {e}")

        if __name__ == "__main__":
        create_admin()
        '''
    
        Path("create_admin.py").write_text(create_test_user_script)
        print("✅ Created admin user creation script")
    
        print("\n🎉 Authentication system consolidated!")
        print("\nNext steps:")
        print("1. Run: python3 create_admin.py")
        print("2. Restart the server")
        print("3. Test login with admin@namaskah.app / admin123")

        if __name__ == "__main__":
        main()
