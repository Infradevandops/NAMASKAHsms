"""Emergency database fix endpoint - adds missing subscription_tier columns"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text
from app.core.database import get_db
from sqlalchemy.orm import Session

router = APIRouter(prefix="/api/emergency", tags=["emergency"])

@router.post("/fix-database")
async def fix_database(db: Session = Depends(get_db)):
    """Emergency endpoint to add missing subscription_tier columns"""
    try:
        # Add subscription_tier column
        db.execute(text("""
            ALTER TABLE users 
            ADD COLUMN IF NOT EXISTS subscription_tier VARCHAR(20) DEFAULT 'freemium'
        """))
        
        # Add tier_upgraded_at column
        db.execute(text("""
            ALTER TABLE users 
            ADD COLUMN IF NOT EXISTS tier_upgraded_at TIMESTAMP
        """))
        
        # Add tier_expires_at column
        db.execute(text("""
            ALTER TABLE users 
            ADD COLUMN IF NOT EXISTS tier_expires_at TIMESTAMP
        """))
        
        # Create index
        db.execute(text("""
            CREATE INDEX IF NOT EXISTS ix_users_subscription_tier 
            ON users(subscription_tier)
        """))
        
        db.commit()
        
        return {
            "success": True,
            "message": "Database fixed - subscription_tier columns added",
            "columns_added": [
                "subscription_tier",
                "tier_upgraded_at", 
                "tier_expires_at"
            ]
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Database fix failed: {str(e)}")
