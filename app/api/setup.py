"""Setup API for production initialization."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.user import User
from app.utils.security import hash_password

router = APIRouter(prefix="/setup", tags=["Setup"])


@router.get("/create-admin")
@router.post("/create-admin")
def create_admin(db: Session = Depends(get_db)):
    """Create admin user for production."""
    try:
        # Check if admin exists
        existing = db.query(User).filter(User.email == "admin@namaskah.app").first()
        if existing:
            return {"message": "Admin already exists"}

        # Create admin
        admin = User(
            email="admin@namaskah.app",
            password_hash=hash_password("Namaskah@Admin2024"),
            credits=1000.0,
            free_verifications=10,
            is_admin=True,
            email_verified=True,
        )

        db.add(admin)
        db.commit()

        return {"message": "Admin created successfully"}

    except Exception as e:
        return {"error": str(e)}


@router.get("/test-user")
@router.post("/test-user")
def create_test_user(db: Session = Depends(get_db)):
    """Create test user for registration testing."""
    try:
        # Check if test user exists
        existing = db.query(User).filter(User.email == "test@namaskah.app").first()
        if existing:
            return {"message": "Test user already exists"}

        # Create test user
        test_user = User(
            email="test@namaskah.app",
            password_hash=hash_password("Test123456"),
            credits=100.0,
            free_verifications=5,
            is_admin=False,
            email_verified=True,
        )

        db.add(test_user)
        db.commit()

        return {
            "message": "Test user created successfully",
            "credentials": {"email": "test@namaskah.app", "password": "Test123456"},
        }

    except Exception as e:
        return {"error": str(e)}


@router.get("/test-registration")
def test_registration_flow(db: Session = Depends(get_db)):
    """Test user registration functionality."""
    try:
        # Test database connection
        user_count = db.query(User).count()

        return {
            "message": "Registration system ready",
            "database_connected": True,
            "total_users": user_count,
            "test_credentials": {
                "admin": {
                    "email": "admin@namaskah.app",
                    "password": "Namaskah@Admin2024",
                },
                "test_user": {"email": "test@namaskah.app", "password": "Test123456"},
            },
        }

    except Exception as e:
        return {"error": str(e), "database_connected": False}
