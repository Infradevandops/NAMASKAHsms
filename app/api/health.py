"""Health check endpoint for monitoring and deployment verification."""


import sys
from datetime import datetime
from fastapi import APIRouter, Depends
from sqlalchemy import inspect, text
from app.core.database import get_db

router = APIRouter(tags=["health"])


@router.get("/health")
async def health_check():
    """Basic health check endpoint."""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "4.0.0",
        "python_version": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
    }


@router.get("/health/ready")
async def readiness_check():
    """Readiness check for load balancers."""
    return {"status": "ready"}


@router.get("/health/live")
async def liveness_check():
    """Liveness check for container orchestration."""
    return {"status": "alive"}


@router.get("/health/db")
async def database_health_check(db=Depends(get_db)):
    """Check database schema health."""
    try:
        engine = db.get_bind()
        inspector = inspect(engine)
        columns = [col["name"] for col in inspector.get_columns("verifications")]
        has_idempotency = "idempotency_key" in columns

        return {
            "status": "healthy" if has_idempotency else "degraded",
            "database": "connected",
            "schema_version": "4.0.0",
            "idempotency_key_present": has_idempotency,
            "message": (
                "All systems operational" if has_idempotency else "Database migration pending - verifications will fail"
            ),
        }
    except Exception as e:
        return {"status": "error", "database": "error", "message": str(e)[:100]}


@router.post("/health/db/fix")
async def fix_database_schema(db=Depends(get_db)):
    """Fix database schema - add missing columns."""
    try:
        engine = db.get_bind()
        inspector = inspect(engine)
        columns = [col["name"] for col in inspector.get_columns("verifications")]
        fixes = []

        if "idempotency_key" not in columns:
            with engine.connect() as conn:
                conn.execute(text("ALTER TABLE verifications ADD COLUMN idempotency_key VARCHAR"))
                conn.execute(text("CREATE INDEX ix_verifications_idempotency_key ON verifications (idempotency_key)"))
                conn.commit()
                fixes.append("Added idempotency_key column and index")

        return {
            "status": "success",
            "fixes_applied": fixes if fixes else ["No fixes needed"],
            "message": "Database schema updated",
        }
    except Exception as e:
        return {"status": "error", "message": str(e)[:200]}
